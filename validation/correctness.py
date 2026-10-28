"""Run reproducible corruption experiments without generating new agent runs.

Evaluator contract: evaluate(task: dict) -> {"passed": bool, "checks":
{"schema": bool, "groundedness": bool, "executability": bool}}.
Only the task is passed to evaluators; mutation metadata stays in the harness.
"""

import argparse
from collections import Counter
from copy import deepcopy
import csv
import importlib
import json
from pathlib import Path
import random


CHECKS = ("schema", "groundedness", "executability")


def verdict(evaluator, task):
    """Reject malformed verdicts; evaluator crashes must not count as detection."""
    result = evaluator(deepcopy(task))
    if not isinstance(result, dict) or type(result.get("passed")) is not bool:
        raise ValueError("Evaluator must return a dictionary with boolean 'passed'")
    checks = result.get("checks")
    if not isinstance(checks, dict) or any(type(checks.get(c)) is not bool for c in CHECKS):
        raise ValueError(f"Evaluator must return boolean checks: {CHECKS}")
    if result["passed"] != all(checks[c] for c in CHECKS):
        raise ValueError("'passed' must equal all three checks passing")
    return {"passed": result["passed"], "checks": {c: checks[c] for c in CHECKS}}


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


def run_experiment(manifest, evaluator, rates=(0, .1, .25, .5, 1), seed=42):
    """Each campaign corrupts a nested subset of initially passing tasks.

Rates apply to eligible tasks, not individual calls. The score denominator is
always the entire input dataset, including baseline failures. One mutation per
task is applied in each campaign. Campaigns isolate corruption kinds.
"""
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

    baseline = {key: verdict(evaluator, task) for key, task in tasks.items()}
    baseline_passes = sum(v["passed"] for v in baseline.values())
    clean_ids = [key for key, label in labels.items() if label]
    false_positives = sum(not baseline[key]["passed"] for key in clean_ids)
    campaigns = {}
    for mutation in manifest["mutations"]:
        key, kind, check = mutation["task_id"], mutation["kind"], mutation["expected_check"]
        if key not in tasks or check not in CHECKS or not isinstance(kind, str) or not kind:
            raise ValueError("Mutation has an invalid task, kind, or expected check")
        candidate = deepcopy(tasks[key])
        replace_at(candidate, mutation["path"], mutation["replacement"])
        group = campaigns.setdefault(kind, {})
        if key in group:
            raise ValueError("Use at most one mutation per task in each campaign")
        group[key] = mutation
    if not campaigns:
        raise ValueError("At least one mutation campaign is required")

    rows, audit, exclusions = [], [], []
    for kind, group in sorted(campaigns.items()):
        eligible = sorted(key for key in group if baseline[key]["passed"])
        exclusions.extend({"kind": kind, "task_id": key, "reason": "baseline_failed"}
                          for key in sorted(group) if key not in eligible)
        random.Random(seed).shuffle(eligible)
        for rate in rates:
            count = int(len(eligible) * rate + .5)
            selected = set(eligible[:count])
            outcomes = dict(baseline)
            detected = targeted = 0
            clean_failed = clean_count = 0
            failures = Counter()
            for key in tasks:
                mutation = group.get(key) if key in selected else None
                if mutation:
                    changed = deepcopy(tasks[key])
                    original = replace_at(changed, mutation["path"], mutation["replacement"])
                    outcomes[key] = verdict(evaluator, changed)
                    detected += not outcomes[key]["passed"]
                    targeted += not outcomes[key]["checks"][mutation["expected_check"]]
                else:
                    original = None
                    if labels.get(key) is True:
                        clean_count += 1
                        clean_failed += not outcomes[key]["passed"]
                for check, passed in outcomes[key]["checks"].items():
                    failures[check] += not passed
                audit.append({
                    "kind": kind, "rate": rate, "task_id": key,
                    "corrupted": mutation is not None,
                    "mutation": ({**deepcopy(mutation), "original": original} if mutation else None),
                    "baseline": baseline[key], "result": outcomes[key],
                })
            observed = sum(v["passed"] for v in outcomes.values()) / len(tasks)
            expected = (baseline_passes - count) / len(tasks)
            rows.append({
                "kind": kind, "requested_rate": rate, "eligible_tasks": len(eligible),
                "corrupted_tasks": count, "effective_dataset_rate": count / len(tasks),
                "expected_score": expected, "observed_score": observed,
                "detected": detected, "detection_rate": detected / count if count else None,
                "targeted_check_detection_rate": targeted / count if count else None,
                "false_positive_rate": clean_failed / clean_count if clean_count else None,
                "check_failures": dict(failures),
                "passed": bool(eligible) and detected == count and targeted == count
                          and abs(observed - expected) < 1e-12,
            })
    exercised = all(any(r["kind"] == kind and r["corrupted_tasks"] for r in rows)
                    for kind in campaigns)
    return {
        "seed": seed, "task_count": len(tasks), "baseline_score": baseline_passes / len(tasks),
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
            checks["schema"] = False
            continue
        customer = state["customers"].get(args["customer_id"])
        if customer is None:
            checks["groundedness"] = False
            continue
        if name == "verify":
            customer["verified"] = True
        elif not customer["verified"]:
            checks["executability"] = False
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
            ("unknown_tool", "schema", ["actions", 0, "name"], "nonexistent_tool"),
            ("wrong_type", "schema", ["actions", 0, "arguments", "customer_id"], 123),
            ("missing_entity", "groundedness", ["actions", 1, "arguments", "customer_id"], "absent"),
            ("broken_precondition", "executability", ["actions"], list(reversed(actions))),
        ]
        for kind, check, path, replacement in cases:
            mutations.append({"task_id": key, "kind": kind, "expected_check": check,
                              "path": path, "replacement": replacement})
    return {"tasks": tasks, "mutations": mutations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Normalized manifest JSON")
    parser.add_argument("--demo", action="store_true", help="Run 20 controlled fixture tasks")
    parser.add_argument("--evaluator", help="Importable module:function implementing the contract")
    parser.add_argument("--rates", nargs="+", type=float, default=[0, .1, .25, .5, 1])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("output/correctness-validation"))
    args = parser.parse_args()
    if args.demo == bool(args.input):
        parser.error("Choose exactly one of --demo or --input")
    if not args.demo and not args.evaluator:
        parser.error("--input requires --evaluator module:function")
    try:
        manifest = demo_manifest() if args.demo else json.loads(args.input.read_text())
        evaluator = reference_evaluator
        if args.evaluator:
            module, function = args.evaluator.split(":", 1)
            evaluator = getattr(importlib.import_module(module), function)
        report = run_experiment(manifest, evaluator, args.rates, args.seed)
        report["evaluator"] = args.evaluator or "validation.correctness:reference_evaluator"
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
              f"{'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
        return 0 if report["passed"] else 1
    except Exception as error:
        # Crashes, missing data, and invalid verdicts are experiment errors, not
        # evidence that a corrupted trajectory was successfully detected.
        parser.exit(2, f"Validation error: {type(error).__name__}: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
