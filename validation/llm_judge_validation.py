"""Run semantic correctness controls and score reference-task samples."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random

from evaluation.llm_judge import Judge, synthetic_evidence, tau2_evidence
from evaluation.synthetic import load_dataset as load_synthetic
from evaluation.tau2.adapter import DOMAINS, load_dataset as load_tau2
from validation.correctness_checker import LLM_CHECKS, run_experiment, verdict
from validation.reporting import write_reports


def control_manifest():
    """Construct independently labeled positives and single-field semantic defects."""
    tasks, mutations = [], []
    for item in ("an invoice", "an expense claim", "a purchase request"):
        task = {
            "request": f"Record {item} for review. Do not approve it.",
            "milestone": "Record the item for review without approving it.",
            "expected_outcome": "The item is recorded for review and is not approved.",
            "policy": "Get explicit submitter consent before calling record_for_review.",
            "conversation": "The submitter explicitly consents to recording the item for review.",
            "reference_workflow": "Call record_for_review once. Do not approve the item.",
            "tools": "record_for_review records the item as pending review without approving it. "
                     "The item exists and is eligible for recording.",
        }
        tasks.append({"id": item, "expected_pass": True, "task": task})
        for check, field, replacement in (
            ("task_consistency", "milestone", "The item must be approved before it is recorded."),
            ("expected_outcome", "expected_outcome", "The item is approved and marked final."),
            ("policy_compliance", "conversation", "The submitter has not been asked for consent."),
            ("workflow_feasibility", "tools", "record_for_review can only record archived items. "
             "This item is active, and no tool can archive it."),
        ):
            mutations.append({
                "task_id": item, "kind": check, "expected_check": check,
                "path": [field], "replacement": replacement,
            })
    return {"dataset": "Constructed semantic controls", "tasks": tasks, "mutations": mutations,
            "label_provenance": "Clean and corrupted expectations declared in control_manifest before judging."}


def score_dataset(manifest, adapter, judge, limit, seed):
    entries = manifest["tasks"]
    if limit and len(entries) > limit:
        entries = random.Random(seed).sample(entries, limit)
    inputs = [adapter(entry["task"]) for entry in entries]
    results = []
    for entry, task in zip(entries, inputs, strict=True):
        try:
            results.append(verdict(judge, task, LLM_CHECKS, "llm"))
        except ValueError as error:
            raise ValueError(f"{manifest['dataset']}/{entry['id']}: {error}") from error
    judgments = {entry["id"]: result for entry, result in zip(entries, results, strict=True)}
    return {
        "dataset": manifest["dataset"], "population": len(manifest["tasks"]),
        "sources": manifest["sources"], "mean_score": sum(r["score"] for r in results) / len(results),
        "score_distribution": distribution(results), "judgments": judgments,
    }


def distribution(results):
    return {name: dict(Counter(str(float(r["checks"][name])) for r in results))
            for name in LLM_CHECKS}


def run(root, tau_root, judge, output, limit=1, seed=42, controls_only=False):
    if limit < 0:
        raise ValueError("Sample limit must be nonnegative (0 selects all tasks)")
    output = Path(output)
    manifest = control_manifest()
    with ThreadPoolExecutor(max_workers=5) as pool:
        controls_run = pool.submit(run_experiment, manifest, judge, (0, 1/3, 2/3, 1), seed, "llm")
        datasets = []
        if not controls_only:
            for path in sorted((Path(root) / "data").glob("*/test_cases.json")):
                datasets.append(pool.submit(score_dataset, load_synthetic(path.parent),
                                            synthetic_evidence, judge, limit, seed))
        if tau_root and not controls_only:
            for domain in DOMAINS:
                datasets.append(pool.submit(score_dataset, load_tau2(tau_root, domain),
                                            tau2_evidence, judge, limit, seed))
        controls = controls_run.result()
        controls["evaluator"] = "evaluation.llm_judge:Judge"
        controls["judge"] = judge.provenance
        write_reports(controls, manifest, output / "controls")
        datasets = [job.result() for job in datasets]

    report = {
        "judge": judge.provenance, "seed": seed, "limit_per_domain": limit,
        "controls": controls, "datasets": datasets,
    }
    (output / "judge_report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls-only", action="store_true", help="Use only constructed fixtures")
    parser.add_argument("--tau-root", type=Path, help="Include the three τ²-bench base splits")
    parser.add_argument("--limit", type=int, default=1, help="Seeded sample per domain; 0 selects all")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = run(root, args.tau_root, Judge.from_env(), args.output,
                 args.limit, args.seed, controls_only=args.controls_only)
    print(f"Controls: {report['controls']['status']}")
    for dataset in report["datasets"]:
        print(f"{dataset['dataset']}: {dataset['mean_score']:.1%} "
              f"({len(dataset['judgments'])}/{dataset['population']} tasks)")
    print(args.output / "judge_report.json")
    return {"pass": 0, "fail": 1, "inconclusive": 3}[report["controls"]["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
