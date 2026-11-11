import csv
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation.correctness_checker import demo_manifest, reference_evaluator, run_experiment
from validation.reporting import render_markdown, terminal_summary, write_reports


def undetected_corruption(task):
    """External-evaluator fixture which intentionally misses every defect."""
    from validation.correctness_checker import CHECKS
    return {"checks": dict.fromkeys(CHECKS, 1)}


class ReportingTests(unittest.TestCase):
    def test_artifacts_and_terminal_share_metrics(self):
        manifest = demo_manifest(20)
        report = run_experiment(manifest, reference_evaluator)
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, manifest, directory)
            saved = json.loads((Path(directory) / "report.json").read_text())
            with (Path(directory) / "summary.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), len(report["campaigns"]))
            self.assertEqual(float(rows[-1]["observed_score"]), saved["campaigns"][-1]["observed_score"])
            self.assertIn("20/20", terminal_summary(report, directory))
            self.assertIn("# Correctness evaluation report", (Path(directory) / "report.md").read_text())
            self.assertIn("separate from the dataset score", render_markdown(report))

    def test_statuses_unavailable_and_bounded_findings(self):
        report = run_experiment(demo_manifest(), reference_evaluator)
        report["baseline_false_positive_rate"] = None
        report["clean_labeled_tasks"] = 0
        for status in ("pass", "fail", "inconclusive", "not_run"):
            report["status"] = status
            text = terminal_summary(report, "/tmp/report")
            self.assertIn(status.replace('_', ' ').upper(), text)
            self.assertIn("Not evaluated (0 labeled)", text)
            self.assertIn(status.replace('_', ' ').upper(), render_markdown(report))
        limited = deepcopy(report)
        limited["baseline_summary"]["checks"]["references"].update(unavailable=3, blocked=2)
        self.assertIn("3/20 unavailable (2 blocked)", terminal_summary(limited, "/tmp/report"))

    def test_baseline_only_report_has_task_csv(self):
        from validation.reporting import evaluate_dataset
        manifest = demo_manifest(2)
        report = evaluate_dataset(manifest, reference_evaluator)
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, manifest, directory)
            with (Path(directory) / "summary.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertIn("corruption validation was not run", render_markdown(report))

    def test_experiment_error_has_diagnostics_and_no_completion_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "input.json"
            manifest.write_text(json.dumps(demo_manifest(1)))
            result = subprocess.run([sys.executable, "-m", "validation.correctness_checker", "--input", str(manifest),
                                     "--evaluator", "missing_evaluator_for_test:evaluate", "--output", directory],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Diagnostics:", result.stderr)
            self.assertNotIn("Validation: PASS", result.stdout)
            self.assertEqual(json.loads((Path(directory) / "error.json").read_text())["status"], "error")

    def test_cli_failure_and_inconclusive_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "input.json"
            manifest.write_text(json.dumps(demo_manifest(1)))
            failure = subprocess.run([sys.executable, "-m", "validation.correctness_checker", "--input", str(manifest),
                                     "--evaluator", "validation.test_reporting:undetected_corruption", "--output", directory],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(failure.returncode, 1)
            self.assertIn("Validation: FAIL", failure.stdout)
            inconclusive = subprocess.run([sys.executable, "-m", "validation.correctness_checker", "--demo", "--rates", "0", "--output", directory],
                                         capture_output=True, text=True, check=False)
            self.assertEqual(inconclusive.returncode, 3)
            self.assertIn("Validation: INCONCLUSIVE", inconclusive.stdout)
