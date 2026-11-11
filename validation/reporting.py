"""One report model, readable Markdown, compact terminal output, and CSV."""

from collections import Counter
import csv
import json
from pathlib import Path


def percentage(value):
    return "Not evaluated" if value is None else f"{value:.1%}"


def baseline_summary(results, categories):
    """Describe evaluated coverage separately from passing applicable checks."""
    values = list(results.values())
    count = len(values)
    outcomes = Counter(r.get("outcome", {}).get("status", "not_evaluated") for r in values)
    return {
        "passed_tasks": sum(r["passed"] for r in values),
        "task_pass_rate": sum(r["passed"] for r in values) / count,
        "fully_evaluated_tasks": sum(r.get("fully_evaluated", all(v is not None for v in r["checks"].values())) for r in values),
        "checks": {c: {
            "failed": sum(r["checks"][c] is not None and r["checks"][c] < 1 for r in values),
            "evaluated": sum(r["checks"][c] is not None for r in values),
            "unavailable": sum(r["checks"][c] is None for r in values),
            "blocked": sum(r.get("coverage", {}).get(c, {}).get("status") == "blocked" for r in values),
        } for c in categories},
        "outcomes": {k: outcomes[k] for k in ("pass", "fail", "not_evaluated")},
        "outcome_uncovered": sorted({item for r in values for item in r.get("outcome", {}).get("uncovered", [])}),
    }


def evaluate_dataset(dataset, evaluator, seed=42):
    """Evaluate references once; this is not a corruption-validation verdict."""
    from validation.correctness_checker import CHECKS, verdict
    results = {entry["id"]: verdict(evaluator, entry["task"]) for entry in dataset["tasks"]}
    if not results:
        raise ValueError("At least one task is required")
    if len(results) != len(dataset["tasks"]):
        raise ValueError("Task IDs must be unique")
    labels = [entry["id"] for entry in dataset["tasks"] if entry.get("expected_pass") is True]
    return {"status": "not_run", "passed": None, "mode": "deterministic", "seed": seed,
            "categories": CHECKS, "task_count": len(results), "baseline_results": results,
            "baseline_score": sum(r["score"] for r in results.values()) / len(results),
            "baseline_summary": baseline_summary(results, CHECKS), "clean_labeled_tasks": len(labels),
            "baseline_false_positive_rate": sum(not results[k]["passed"] for k in labels) / len(labels) if labels else None,
            "campaigns": [], "audit": [], "excluded_mutations": [],
            "unexercised_campaigns": [], "metadata": metadata(dataset)}


def metadata(manifest):
    return {k: v for k, v in manifest.items() if k not in ("tasks", "mutations")}


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def findings(report, limit=3):
    """Prefer unexpected corruption behavior, then baseline task defects."""
    selected, seen = [], set()
    candidates = []
    for item in report.get("audit", []):
        if not item["corrupted"]:
            continue
        expected = {**item["baseline"]["checks"],
                    **item["mutation"].get("expected_checks", {item["mutation"]["expected_check"]: 0})}
        if item["result"]["checks"] != expected:
            candidates.append({"task_id": item["task_id"], "campaign": item["kind"],
                               "expected": expected, "observed": item["result"]["checks"],
                               "message": "Corruption did not produce the declared check vector"})
    for task_id, result in report["baseline_results"].items():
        for check, evidence in result.get("evidence", {}).items():
            for problem in evidence:
                candidates.append({"task_id": task_id, "check": check, **problem})
        if result.get("outcome", {}).get("status") == "fail":
            candidates.append({"task_id": task_id, "check": "outcome", "message": "Independent final-state assertion failed"})
    for item in candidates:
        key = (item["task_id"], item.get("check"), item.get("campaign"))
        if key not in seen:
            selected.append(item)
            seen.add(key)
        if len(selected) == limit:
            break
    return selected


def render_markdown(report):
    summary = report.get("baseline_summary") or baseline_summary(report["baseline_results"], report["categories"])
    status = report["status"]
    meaning = {"pass": "The evaluator detected the declared corruptions with the expected score changes.",
               "fail": "Corruption behavior differed from expectations or a labeled clean task failed.",
               "inconclusive": "At least one campaign did not exercise an eligible corruption.",
               "not_run": "Baseline evaluation completed; corruption validation was not run."}[status]
    count = report["task_count"]
    meta = report.get("metadata", {})
    lines = ["# Correctness evaluation report", "", f"**Validation: {status.replace('_', ' ').upper()}** — {meaning}", "",
             "Validation status describes the evaluator experiment; it is separate from the dataset score.", "",
             "## Baseline dataset results", "", f"Dataset: **{_cell(meta.get('dataset', report.get('input', 'controlled fixtures')))}**. "
             f"Subject: {_cell(meta.get('subject', 'controlled fixtures'))}.", "",
             f"- Operational score: **{percentage(report['baseline_score'])}** (mean applicable-check score per task).",
             f"- Passing applicable checks: **{summary['passed_tasks']}/{count} ({percentage(summary['task_pass_rate'])})**.",
             f"- Fully evaluated across configured checks: **{summary['fully_evaluated_tasks']}/{count}**.",
             f"- Clean-task false positives: **{percentage(report.get('baseline_false_positive_rate'))}** "
             f"({report.get('clean_labeled_tasks', 0)} labeled clean tasks).", "",
             "Passing applicable checks does not establish that the user's request was satisfied.", "",
             "## Checks and coverage", "", "| Check | Failures / evaluated | Unavailable | Blocked |",
             "| --- | ---: | ---: | ---: |"]
    for name, values in summary["checks"].items():
        lines.append(f"| {_cell(name)} | {values['failed']}/{values['evaluated']} | {values['unavailable']} | {values['blocked']} |")
    lines += ["", "Unavailable checks are excluded from scores; blocked checks are a subset of unavailable checks.",
              "", "## Corruption campaigns", "",
              "Rates select nested subsets of eligible tasks, not individual calls. Detection counts only corrupted tasks.", ""]
    if meta.get("label_provenance"):
        lines += [f"Clean-label basis: {_cell(meta['label_provenance'])}.", ""]
    if report["campaigns"]:
        lines += ["| Campaign | Requested | Corrupted / eligible | Eligible rate | Dataset rate | Target detection | Expected score | Observed score | Vectors matched | Clean false positives | Result |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
        for row in report["campaigns"]:
            n = row["corrupted_tasks"]
            label = "PASS" if row["passed"] else ("INCONCLUSIVE" if not row["eligible_tasks"] else "FAIL")
            lines.append(f"| {_cell(row['kind'])} | {percentage(row['requested_rate'])} | {n}/{row['eligible_tasks']} | "
                         f"{percentage(row.get('effective_eligible_rate'))} | {percentage(row['effective_dataset_rate'])} | "
                         f"{percentage(row['targeted_check_detection_rate'])} ({row.get('targeted_detected', 0)}/{n}) | "
                         f"{percentage(row['expected_score'])} | {percentage(row['observed_score'])} | "
                         f"{row['expected_check_vectors_matched']}/{n} | {percentage(row['false_positive_rate'])} | {label} |")
    else:
        lines.append("Not run.")
    exclusions = Counter(item["reason"] for item in report.get("excluded_mutations", []))
    lines += ["", f"Mutation exclusions: {_cell(dict(exclusions)) or 'none'}.",
              f"Unexercised campaigns: {_cell(', '.join(report.get('unexercised_campaigns', []))) or 'none'}.",
              "", "## Representative findings", ""]
    samples = findings(report, 10)
    if not samples:
        lines.append("No baseline defects or unexpected corruption check vectors were reported.")
    for sample in samples:
        lines += [f"- Task **{_cell(sample['task_id'])}**, check/campaign **{_cell(sample.get('check', sample.get('campaign')))}**: "
                  f"{_cell(sample.get('message', 'Check failed'))} "
                  f"(action: {_cell(sample.get('action', sample.get('action_id', 'task structure')))})."]
        if "expected" in sample:
            lines.append(f"  Expected: `{_cell(sample['expected'])}`; observed: `{_cell(sample['observed'])}`.")
    lines += ["", "Detailed per-action evidence, output previews, and bounded state differences are in report.json.",
              "", "## Outcome checking", ""]
    outcomes = summary["outcomes"]
    lines += [f"Independent outcome assertions: **{outcomes['pass']} passed, {outcomes['fail']} failed, "
              f"{outcomes['not_evaluated']} not evaluated**.", "",
              "Outcomes are separate from the operational score. Reference replay is never compared against itself as proof of success."]
    lines += [f"- {_cell(item)}" for item in summary["outcome_uncovered"]]
    limits = sorted({str(item) for r in report["baseline_results"].values()
                     for values in r.get("coverage_limits", {}).values() for item in values})
    if limits:
        lines += ["", "Additional coverage limits:", ""] + [f"- {_cell(item)}" for item in limits]
    source = meta.get("sources", {})
    lines += ["", "## Reproduction and artifacts", "", f"- Seed: {report['seed']}.",
              f"- Evaluator: {_cell(report.get('evaluator', 'external evaluator'))}.",
              "- Files: [JSON evidence](report.json), [CSV summary](summary.csv), [input manifest](manifest.json).",
              "- Shared benchmark assets must remain available at the paths recorded in the manifest.",
              f"- Benchmark revision: {_cell(source.get('revision') or 'Not recorded / external data')}.",
              f"- Split: {_cell(meta.get('split', 'Not applicable'))}."]
    if meta.get("snapshot_provenance"):
        lines.append(f"- Snapshot: {_cell(meta['snapshot_provenance'])}.")
    if meta.get("task_drift"):
        lines.append(f"- Explicitly allowed task drift: {_cell(', '.join(meta['task_drift']))}.")
    if meta.get("coverage_note"):
        lines.append(f"- Coverage: {_cell(meta['coverage_note'])}.")
    lines += ["", "Full source paths/hashes, selected IDs, labels, and exclusions are retained in the JSON artifacts.", ""]
    return "\n".join(lines)


def terminal_summary(report, output):
    summary = report["baseline_summary"]
    count = report["task_count"]
    name = report.get("metadata", {}).get("dataset", "controlled fixtures")
    lines = [f"Validation: {report['status'].replace('_', ' ').upper()} | {name} | {count} tasks",
             f"Baseline score: {percentage(report['baseline_score'])} | "
             f"Passing checks: {summary['passed_tasks']}/{count} ({percentage(summary['task_pass_rate'])})",
             f"Fully evaluated: {summary['fully_evaluated_tasks']}/{count} | Clean false positives: "
             f"{percentage(report.get('baseline_false_positive_rate'))} ({report.get('clean_labeled_tasks', 0)} labeled)"]
    kinds = sorted({r["kind"] for r in report["campaigns"]})
    if kinds:
        lines += ["Campaign                       Target detection across rates   Score agreement  Status"]
    for kind in kinds:
        rows = [r for r in report["campaigns"] if r["kind"] == kind]
        n = sum(r["corrupted_tasks"] for r in rows)
        detected = sum(r.get("targeted_detected", round((r["targeted_check_detection_rate"] or 0) * r["corrupted_tasks"])) for r in rows)
        agreement = all(abs(r["expected_score"] - r["observed_score"]) < 1e-12 for r in rows)
        label = "INCONCLUSIVE" if not n else ("PASS" if all(r["passed"] for r in rows) else "FAIL")
        lines.append(f"{kind.replace('_', ' '):<30} {percentage(detected / n if n else None):>13} ({detected}/{n})    "
                     f"{'yes' if agreement else 'NO':>8}         {label}")
    gaps = [f"{c}: {v['unavailable']}/{count} unavailable ({v['blocked']} blocked)"
            for c, v in summary["checks"].items() if v["unavailable"]]
    if gaps:
        lines.append("Coverage: " + "; ".join(gaps))
    if report.get("metadata", {}).get("label_provenance"):
        lines.append("Clean-label basis: " + report["metadata"]["label_provenance"])
    outcomes = summary["outcomes"]
    lines.append(f"Separate outcomes: {outcomes['pass']} pass, {outcomes['fail']} fail, {outcomes['not_evaluated']} not evaluated")
    for finding in findings(report, 3):
        lines.append(f"  Task {finding['task_id']}: {finding.get('check', finding.get('campaign'))}: {finding['message']}")
    if report["status"] == "pass":
        lines.append("Validation passed = declared corruptions detected; this is not the dataset score.")
    lines += [f"Readable report: {Path(output) / 'report.md'}", f"Detailed evidence: {Path(output) / 'report.json'}",
              f"CSV summary: {Path(output) / 'summary.csv'}"]
    return "\n".join(lines)


def write_reports(report, manifest, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report.setdefault("metadata", metadata(manifest))
    report.setdefault("baseline_summary", baseline_summary(report["baseline_results"], report["categories"]))
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    (output / "report.md").write_text(render_markdown(report))
    rows = report["campaigns"] or [{"task_id": key, "score": value["score"], "passed": value["passed"],
                                     "checks": value["checks"]} for key, value in report["baseline_results"].items()]
    rows = [{k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()} for row in rows]
    with (output / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "error.json").unlink(missing_ok=True)


def write_error(error, output):
    """Separate error artifact; never overwrite completed reports with success."""
    path = Path(output) / "error.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": "error", "type": type(error).__name__, "message": str(error)}, indent=2) + "\n")
    return path
