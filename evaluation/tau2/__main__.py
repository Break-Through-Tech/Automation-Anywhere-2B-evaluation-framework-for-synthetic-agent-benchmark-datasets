"""CLI for offline reference evaluation and controlled evaluator validation."""

import argparse
import json
from pathlib import Path

from .adapter import DOMAINS, fingerprint, load_dataset
from .evaluator import evaluate
from validation.correctness_checker import run_experiment
from validation.reporting import evaluate_dataset, terminal_summary, write_error, write_reports
from validation.tau2_corruptions import build_corruption_manifest, clean_controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--domain", choices=DOMAINS, default="retail")
    parser.add_argument("--split", default="base")
    parser.add_argument("--task-ids", nargs="+")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--validate-corruptions", action="store_true")
    parser.add_argument("--controls", action="store_true", help="Use 20 independently constructed controls for the selected domain")
    parser.add_argument("--labels", type=Path, help="JSON task-ID map: {id: {expected_pass: bool, reviewer: str}}")
    parser.add_argument("--rates", type=float, nargs="+", default=[0, .1, .25, .5, 1])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("output/tau2-correctness"))
    args = parser.parse_args()
    try:
        # Upstream uses loguru for verbose per-call logging. Silence only tau2;
        # actionable evaluator errors still propagate to the error artifact.
        from loguru import logger
        logger.disable("tau2")
        dataset = load_dataset(args.benchmark_root, args.domain, args.split, args.task_ids, args.limit)
        if args.controls:
            dataset = clean_controls(dataset)
        if args.labels:
            labels = json.loads(args.labels.read_text())
            ids = {entry["id"] for entry in dataset["tasks"]}
            if not isinstance(labels, dict) or labels.keys() - ids:
                raise ValueError("Labels must map selected task IDs to reviewed labels")
            for entry in dataset["tasks"]:
                if entry["id"] in labels:
                    label = labels[entry["id"]]
                    if (not isinstance(label, dict) or type(label.get("expected_pass")) is not bool
                            or not isinstance(label.get("reviewer"), str) or not label["reviewer"].strip()):
                        raise ValueError("Labels require boolean expected_pass and reviewer")
                    entry.update(expected_pass=label["expected_pass"], label_provenance=label)
            dataset["labels_source"] = {"path": str(args.labels.resolve()), "sha256": fingerprint(args.labels)}
        manifest = build_corruption_manifest(dataset) if args.validate_corruptions else dataset
        report = (run_experiment(manifest, evaluate, args.rates, args.seed) if args.validate_corruptions else
                  evaluate_dataset(dataset, evaluate, args.seed))
        report["evaluator"] = "evaluation.tau2:evaluate"
        write_reports(report, manifest, args.output)
        print(terminal_summary(report, args.output))
        return {"pass": 0, "not_run": 0, "fail": 1, "inconclusive": 3}[report["status"]]
    except Exception as error:
        try:
            diagnostic = str(write_error(error, args.output))
        except OSError:
            diagnostic = "unavailable (output directory is not writable)"
        parser.exit(2, f"Evaluation error: {type(error).__name__}: {error}\nDiagnostics: {diagnostic}\n")


if __name__ == "__main__":
    raise SystemExit(main())
