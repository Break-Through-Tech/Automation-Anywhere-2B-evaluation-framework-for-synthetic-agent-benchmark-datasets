"""Framework for validating correctness evaluators with controlled corruptions.

This harness evaluates original tasks, applies known mutations, and checks
per-category detection and expected score changes. It does not generate agent
runs. Dataset evaluators and LLM judges are separate integrations; they are not
included in this folder. The built-in --demo remains a small executable fixture,
not a benchmark adapter. External evaluators can be supplied with --evaluator.

Evaluator contract: evaluate(task: dict) -> {"checks": {category: score}}.
Deterministic scores are 0 or 1; LLM scores are 0, 0.5, or 1. Use None
for an inapplicable check. Every configured category must be present and at
least one must be applicable. The harness calculates each task's mean over
applicable checks, then averages task scores. Run each evaluator separately.

Mutations specify expected_check and optionally expected_checks: overrides to
baseline check scores describing the known expected result of the corruption.
Without overrides, only expected_check is expected to become 0. Expected score
drops therefore follow check-level partial credit, not whole-task rejection.
"""

import argparse
from collections import Counter
from copy import deepcopy
import csv
import importlib
import json
from pathlib import Path
import random


CHECKS = ("schema", "signatures", "references", "output_consistency")
LLM_CHECKS = ("task_consistency", "expected_outcome", "policy_compliance", "workflow_feasibility")


def score_checks(checks, categories, mode):
    if not isinstance(checks, dict) or set(checks) != set(categories):
        raise ValueError(f"Evaluator must return exactly these checks: {categories}")
    allowed = (0, 1) if mode == "deterministic" else (0, .5, 1)
    applicable = []
    for value in checks.values():
        if value is None:
            continue
        if not isinstance(value, (int, float)) or value not in allowed:
            raise ValueError(f"{mode} scores must be {allowed}, or None for inapplicable")
        applicable.append(value)
    if not applicable:
        raise ValueError("At least one check must be applicable")
    return sum(applicable) / len(applicable)


def verdict(evaluator, task, categories=CHECKS, mode="deterministic"):
    """Validate scores; evaluator crashes are experiment errors, not detection."""
    result = evaluator(deepcopy(task))
    if not isinstance(result, dict):
        raise ValueError("Evaluator must return a dictionary containing checks")
    checks = result.get("checks")
    score = score_checks(checks, categories, mode)
    return {**deepcopy(result), "passed": score == 1, "score": score, "checks": deepcopy(checks)}


def replace_at(task, path, replacement):
    """Replace an existing leaf, refusing accidental no-op corruptions."""
    if not isinstance(path, list) or not path:
        raise ValueError("Mutation path must be a nonempty list of keys/indices")
    current = task
    for key in path[:-1]:
        current = current[key]
    original = deepcopy(current[path[-1]])
    if original == replacement:
        raise ValueError("Mutation must change the original value")
    current[path[-1]] = deepcopy(replacement)
    return original


def run_experiment(manifest, evaluator, rates=(0, .1, .25, .5, 1), seed=42, mode="deterministic"):
    """Each campaign corrupts a nested subset of tasks passing its target check.

Rates apply to eligible tasks, not individual calls. Dataset scores average
all task scores, including baseline failures. One mutation per
task is applied in each campaign. Campaigns isolate corruption kinds.
"""
    if mode not in ("deterministic", "llm"):
        raise ValueError("Mode must be deterministic or llm")
    categories = CHECKS if mode == "deterministic" else LLM_CHECKS
    rates = sorted(set(rates))
    if not rates or any(not 0 <= r <= 1 for r in rates):
        raise ValueError("Rates must be finite numbers between 0 and 1")
    entries = manifest["tasks"]
    if not entries:
        raise ValueError("At least one task is required")
    tasks = {}
    labels = {}
    for entry in entries:
        task_id = entry["id"]
        if not isinstance(task_id, str) or task_id in tasks:
            raise ValueError("Task IDs must be unique strings")
        tasks[task_id] = deepcopy(entry["task"])
        if "expected_pass" in entry:
            if type(entry["expected_pass"]) is not bool:
                raise ValueError("expected_pass must be boolean")
            labels[task_id] = entry["expected_pass"]

    baseline = {key: verdict(evaluator, task, categories, mode) for key, task in tasks.items()}
    baseline_total = sum(v["score"] for v in baseline.values())
    clean_ids = [key for key, label in labels.items() if label]
    false_positives = sum(not baseline[key]["passed"] for key in clean_ids)
    campaigns = {}
    for mutation in manifest["mutations"]:
        key, kind, check = mutation["task_id"], mutation["kind"], mutation["expected_check"]
        if key not in tasks or check not in categories or not isinstance(kind, str) or not kind:
            raise ValueError("Mutation has an invalid task, kind, or expected check")
        candidate = deepcopy(tasks[key])
        replace_at(candidate, mutation["path"], mutation["replacement"])
        group = campaigns.setdefault(kind, {})
        if key in group:
            raise ValueError("Use at most one mutation per task in each campaign")
        overrides = mutation.get("expected_checks", {check: 0})
        if not isinstance(overrides, dict) or not overrides or not set(overrides) <= set(categories):
            raise ValueError("expected_checks must override known categories")
        expected_checks = {**baseline[key]["checks"], **overrides}
        expected_score = score_checks(expected_checks, categories, mode)
        if baseline[key]["checks"][check] == 1 and (expected_checks[check] is None
                or expected_checks[check] >= baseline[key]["checks"][check]
                or expected_score >= baseline[key]["score"]):
            raise ValueError("Mutation must lower its target check and task score")
        group[key] = mutation
    if not campaigns:
        raise ValueError("At least one mutation campaign is required")

    rows, audit, exclusions = [], [], []
    for kind, group in sorted(campaigns.items()):
        eligible = sorted(key for key in group
                          if baseline[key]["checks"][group[key]["expected_check"]] == 1)
        exclusions.extend({"kind": kind, "task_id": key, "reason": "target_check_not_passing"}
                          for key in sorted(group) if key not in eligible)
        random.Random(seed).shuffle(eligible)
        for rate in rates:
            count = int(len(eligible) * rate + .5)
            selected = set(eligible[:count])
            outcomes = dict(baseline)
            detected = targeted = expected_matches = 0
            expected_total = baseline_total
            clean_failed = clean_count = 0
            failures = Counter()
            for key in tasks:
                mutation = group.get(key) if key in selected else None
                if mutation:
                    changed = deepcopy(tasks[key])
                    original = replace_at(changed, mutation["path"], mutation["replacement"])
                    outcomes[key] = verdict(evaluator, changed, categories, mode)
                    expected_checks = {**baseline[key]["checks"],
                                       **mutation.get("expected_checks", {mutation["expected_check"]: 0})}
                    expected_total += score_checks(expected_checks, categories, mode) - baseline[key]["score"]
                    expected_matches += outcomes[key]["checks"] == expected_checks
                    detected += outcomes[key]["score"] < baseline[key]["score"]
                    target = mutation["expected_check"]
                    target_score = outcomes[key]["checks"][target]
                    targeted += target_score is not None and target_score < baseline[key]["checks"][target]
                else:
                    original = None
                    if labels.get(key) is True:
                        clean_count += 1
                        clean_failed += not outcomes[key]["passed"]
                for check, passed in outcomes[key]["checks"].items():
                    failures[check] += passed is not None and passed < 1
                audit.append({
                    "kind": kind, "rate": rate, "task_id": key,
                    "corrupted": mutation is not None,
                    "mutation": ({**deepcopy(mutation), "original": original} if mutation else None),
                    "baseline": baseline[key], "result": outcomes[key],
                })
            observed = sum(v["score"] for v in outcomes.values()) / len(tasks)
            expected = expected_total / len(tasks)
            rows.append({
                "kind": kind, "requested_rate": rate, "eligible_tasks": len(eligible),
                "corrupted_tasks": count, "effective_dataset_rate": count / len(tasks),
                "expected_score": expected, "observed_score": observed,
                "expected_check_vectors_matched": expected_matches,
                "detected": detected, "detection_rate": detected / count if count else None,
                "targeted_check_detection_rate": targeted / count if count else None,
                "false_positive_rate": clean_failed / clean_count if clean_count else None,
                "check_failures": dict(failures),
                "passed": bool(eligible) and detected == count and targeted == count
                          and expected_matches == count
                          and abs(observed - expected) < 1e-12,
            })
    exercised = all(any(r["kind"] == kind and r["corrupted_tasks"] for r in rows)
                    for kind in campaigns)
    unexercised = sorted(kind for kind in campaigns
                         if not any(r["kind"] == kind and r["corrupted_tasks"] for r in rows))
    failures_observed = any(not row["passed"] for row in rows if row["eligible_tasks"])
    status = "fail" if failures_observed or false_positives else ("inconclusive" if unexercised else "pass")
    return {
        "status": status, "unexercised_campaigns": unexercised,
        "mode": mode, "categories": categories,
        "seed": seed, "task_count": len(tasks), "baseline_score": baseline_total / len(tasks),
        "baseline_results": baseline,
        "baseline_false_positive_rate": false_positives / len(clean_ids) if clean_ids else None,
        "excluded_mutations": exclusions, "campaigns": rows, "audit": audit,
        "passed": exercised and all(row["passed"] for row in rows)
                  and false_positives == 0,
    }


def reference_evaluator(task):
    """Demo only: replay verify/approve against fresh in-memory customer state.

    This is a small executable fixture environment, not a tau-bench adapter or
    a production correctness metric. Unknown tools/invalid calls are not run.
    """
    state = deepcopy(task["initial_state"])
    checks = dict.fromkeys(CHECKS, True)
    for action in task["actions"]:
        name, args = action.get("name"), action.get("arguments")
        if (name not in ("verify", "approve") or not isinstance(args, dict)
                or set(args) != {"customer_id"} or type(args["customer_id"]) is not str):
            checks["signatures"] = False
            continue
        customer = state["customers"].get(args["customer_id"])
        if customer is None:
            checks["references"] = False
            continue
        if name == "verify":
            customer["verified"] = True
        elif not customer["verified"]:
            checks["output_consistency"] = False
        else:
            customer["approved"] = True
    return {"passed": all(checks.values()), "checks": checks}


def demo_manifest(size=20):
    tasks, mutations = [], []
    for index in range(size):
        key, customer_id = f"task-{index:03}", f"customer-{index:03}"
        actions = [{"name": name, "arguments": {"customer_id": customer_id}}
                   for name in ("verify", "approve")]
        tasks.append({"id": key, "expected_pass": True, "task": {
            "initial_state": {"customers": {customer_id: {"verified": False, "approved": False}}},
            "actions": actions,
        }})
        cases = [
            ("unknown_tool", "signatures", ["actions", 0, "name"], "nonexistent_tool"),
            ("wrong_type", "signatures", ["actions", 0, "arguments", "customer_id"], 123),
            ("missing_entity", "references", ["actions", 1, "arguments", "customer_id"], "absent"),
            ("broken_precondition", "output_consistency", ["actions"], list(reversed(actions))),
        ]
        for kind, check, path, replacement in cases:
            mutation = {"task_id": key, "kind": kind, "expected_check": check,
                        "path": path, "replacement": replacement}
            if kind in ("unknown_tool", "wrong_type"):
                mutation["expected_checks"] = {"signatures": 0, "output_consistency": 0}
            mutations.append(mutation)
    return {"tasks": tasks, "mutations": mutations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Normalized manifest JSON")
    parser.add_argument("--demo", action="store_true", help="Run 20 controlled fixture tasks")
    parser.add_argument("--evaluator", help="Importable module:function implementing the contract")
    parser.add_argument("--rates", nargs="+", type=float, default=[0, .1, .25, .5, 1])
    parser.add_argument("--mode", choices=("deterministic", "llm"), default="deterministic")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("output/correctness-validation"))
    args = parser.parse_args()
    if args.demo == bool(args.input):
        parser.error("Choose exactly one of --demo or --input")
    if not args.demo and not args.evaluator:
        parser.error("--input requires --evaluator module:function")
    if args.mode == "llm" and not args.evaluator:
        parser.error("LLM mode requires an external --evaluator; no LLM judge is built in")
    try:
        manifest = demo_manifest() if args.demo else json.loads(args.input.read_text())
        evaluator = reference_evaluator
        if args.evaluator:
            module, function = args.evaluator.split(":", 1)
            evaluator = getattr(importlib.import_module(module), function)
        report = run_experiment(manifest, evaluator, args.rates, args.seed, args.mode)
        report["evaluator"] = args.evaluator or "validation.correctness_checker:reference_evaluator"
        report["input"] = str(args.input) if args.input else "controlled_demo_fixtures"
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        rows = [{**row, "check_failures": json.dumps(row["check_failures"], sort_keys=True)}
                for row in report["campaigns"]]
        with (args.output / "summary.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Baseline: {report['baseline_score']:.1%}; validation: "
              f"{report['status'].upper()}; report: {args.output / 'report.json'}")
        return 0 if report["passed"] else (3 if report["status"] == "inconclusive" else 1)
    except Exception as error:
        # Crashes, missing data, and invalid verdicts are experiment errors, not
        # evidence that a corrupted trajectory was successfully detected.
        parser.exit(2, f"Validation error: {type(error).__name__}: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
