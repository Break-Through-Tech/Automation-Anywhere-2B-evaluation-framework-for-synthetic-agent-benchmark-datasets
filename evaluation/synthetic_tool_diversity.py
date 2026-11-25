"""Tool Usage Diversity for the synthetic benchmark datasets.

Two call sources:
  expected  - each test case's ``expected_tool_calls`` (offline, same source as
              notebooks/correctness_validation.ipynb section 6)
  live      - real agent traces from data/run_test_cases.py's runner
              (needs OPENAI_API_KEY, BASE_URL, MODEL_NAME in .env)

Usage (from the repo root):
  python -m evaluation.synthetic_tool_diversity                      # expected only
  python -m evaluation.synthetic_tool_diversity --source live        # run agents, save traces, score
  python -m evaluation.synthetic_tool_diversity --source both
  python -m evaluation.synthetic_tool_diversity --source live --traces-only   # re-score saved traces

Outputs go to output/tool_diversity/synthetic/ :
  <dataset>_<source>.json   full report (metrics, per-task calls, perturbation checks)
  summary.csv               one row per dataset x source
  per_tool.csv              per-tool counts and proportions
  comparison.csv            expected vs live per tool (when both sources exist)
  traces/<dataset>.json     saved live traces ({"tasks": [...]}, readable by
                            notebooks/tool_usage_diversity.ipynb)
"""

import argparse
import asyncio
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from correctness_op.deterministic_audit import SYSTEM  # noqa: E402
from evaluation.synthetic import load_dataset  # noqa: E402
from evaluation.tool_usage_diversity import calculate_diversity, validate_perturbations  # noqa: E402

DEFAULT_DATASETS = [
    "healthcare_patient_onboarding",
    "healthcare_prior_authorization",
    "insurance_claims_intake",
    "manufacturing_purchase_to_pay",
]
METRIC = "normalized_tool_usage_diversity"


def inventory_for(dataset):
    """YAML tools plus the built-in system tools, as in the validation notebook."""
    return sorted(dataset["tasks"][0]["task"]["tools"].keys() | SYSTEM.keys())


def names(calls):
    return [c["name"] for c in (calls if isinstance(calls, list) else [])
            if isinstance(c, dict) and isinstance(c.get("name"), str)
            and (c.get("requestor") or "assistant") == "assistant"]


def expected_task_calls(dataset):
    task_calls, unmatched = [], []
    for entry in dataset["tasks"]:
        fixture = entry["task"]["python_fixture"]
        if not fixture:
            unmatched.append(entry["id"])
        calls = (fixture or {}).get("attributes", {}).get("expected_tool_calls")
        task_calls.append({"task_id": entry["id"], "calls": names(calls)})
    return task_calls, unmatched


# ---------- live runs ----------

def serialize_message(message):
    row = {"role": message.type, "content": message.content if isinstance(message.content, str)
           else json.dumps(message.content, default=str)}
    calls = getattr(message, "tool_calls", None)
    if calls:
        row["tool_calls"] = [{"id": c.get("id"), "name": c.get("name"), "args": c.get("args")}
                             for c in calls]
    if message.type == "tool":
        row["name"] = getattr(message, "name", None)
        row["tool_call_id"] = getattr(message, "tool_call_id", None)
    return row


def run_live(dataset_name, trace_path, max_turns):
    data_dir = ROOT / "data"
    sys.path.insert(0, str(data_dir))
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    for key in ("OPENAI_API_KEY", "BASE_URL", "MODEL_NAME"):
        if not os.getenv(key):
            raise SystemExit(f"Missing {key} in .env; live runs need OPENAI_API_KEY, BASE_URL, MODEL_NAME.")
    from langchain_openai import ChatOpenAI
    import run_test_cases as runner

    model = ChatOpenAI(model=os.getenv("MODEL_NAME"), openai_api_key=os.getenv("OPENAI_API_KEY"),
                       openai_api_base=os.getenv("BASE_URL"), temperature=1, reasoning_effort="none")
    cwd = os.getcwd()
    os.chdir(data_dir)  # runner imports "<agent>.test_cases" relative to data/
    try:
        examples = runner.load_local_test_cases([dataset_name]) or []
        tasks = []
        for i, example in enumerate(examples, 1):
            inputs = example["inputs"]
            print(f"[{dataset_name}] {i}/{len(examples)} {inputs['test_id']}", flush=True)
            row = {"task_id": inputs["test_id"], "domain": dataset_name,
                   "expected_tool_sequence": example["outputs"]["expected_tool_sequence"]}
            try:
                result, _ = asyncio.run(runner.run_local_testcases_async(
                    inputs, test_agent_llm_model=model, system_prompt=None, verbose=False,
                    max_turns=max_turns, agent_type="staticremem"))
                row.update(completed=result.completed, turns=result.turns,
                           messages=[serialize_message(m) for m in result.messages])
            except Exception as error:  # keep going; record the failure
                row.update(error=f"{type(error).__name__}: {error}", messages=[])
            tasks.append(row)
    finally:
        os.chdir(cwd)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps({"model": os.getenv("MODEL_NAME"), "tasks": tasks}, indent=2,
                                     default=str) + "\n", encoding="utf-8")
    return trace_path


def live_task_calls(trace_path):
    document = json.loads(trace_path.read_text(encoding="utf-8"))
    task_calls, errors = [], []
    for task in document["tasks"]:
        if task.get("error"):
            errors.append({"task_id": task["task_id"], "error": task["error"]})
        calls, seen = [], set()
        for message in task.get("messages", []):
            if str(message.get("role", "")).lower() not in {"ai", "assistant", "aimessage"}:
                continue
            for call in message.get("tool_calls") or []:
                if call.get("id") and call["id"] in seen:
                    continue
                seen.add(call.get("id"))
                if isinstance(call.get("name"), str):
                    calls.append(call["name"])
        task_calls.append({"task_id": task["task_id"], "calls": calls,
                           "completed": task.get("completed")})
    return task_calls, errors, document.get("model")


# ---------- scoring / output ----------

def score(dataset_name, source, inventory, task_calls, extra):
    counts = Counter(c for t in task_calls for c in t["calls"])
    metrics = calculate_diversity(dict(counts), inventory)
    report = {**metrics, "task_calls": task_calls}
    report["validation"] = validate_perturbations(report, inventory)
    if metrics["recognized_tool_calls"]:
        assert report["validation"]["strict_single_tool"]["passed"], dataset_name
    report["never_called_tools"] = [t for t, n in metrics["tool_call_counts"].items() if n == 0]
    report["configuration"] = {"dataset": dataset_name, "source": source,
                               "reference_tools": inventory,
                               "unknown_tool_policy": "reported and excluded from score", **extra}
    return report


def summary_row(report):
    cfg, val = report["configuration"], report["validation"]
    tasks = report["task_calls"]
    return {
        "dataset": cfg["dataset"], "source": cfg["source"], "tasks": len(tasks),
        "tasks_with_calls": sum(bool(t["calls"]) for t in tasks),
        "reference_tools": report["reference_tool_count"],
        "distinct_tools_used": report["distinct_tools_used"],
        "recognized_calls": report["recognized_tool_calls"],
        "unknown_calls": report["unknown_tool_calls"],
        "raw_entropy": round(report["raw_shannon_entropy"], 4) if report["raw_shannon_entropy"] is not None else None,
        "tool_balance": round(report["tool_balance"], 4) if report["tool_balance"] is not None else None,
        "diversity": round(report[METRIC], 4) if report[METRIC] is not None else None,
        "most_used_tool": val["strict_single_tool"]["selected_tool"],
        "single_tool_perturbation": val["strict_single_tool"][METRIC],
        "single_tool_check_passed": val["strict_single_tool"]["passed"],
        "never_called": ";".join(report["never_called_tools"]),
    }


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datasets", nargs="+", default=DEFAULT_DATASETS)
    parser.add_argument("--source", choices=["expected", "live", "both"], default="expected")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "tool_diversity" / "synthetic")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--traces-only", action="store_true",
                        help="Score existing traces/<dataset>.json instead of re-running agents")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    summaries, per_tool, comparison = [], [], []
    for name in args.datasets:
        dataset = load_dataset(ROOT / "data" / name)
        inventory = inventory_for(dataset)
        reports = {}
        if args.source in ("expected", "both"):
            task_calls, unmatched = expected_task_calls(dataset)
            reports["expected"] = score(name, "expected", inventory, task_calls,
                                        {"unmatched_tasks": unmatched})
        if args.source in ("live", "both"):
            trace = args.output / "traces" / f"{name}.json"
            if not args.traces_only:
                run_live(name, trace, args.max_turns)
            task_calls, errors, model = live_task_calls(trace)
            reports["live"] = score(name, "live", inventory, task_calls,
                                    {"model": model, "trace_file": str(trace), "run_errors": errors})
        for source, report in reports.items():
            (args.output / f"{name}_{source}.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            summaries.append(summary_row(report))
            for tool in inventory:
                per_tool.append({"dataset": name, "source": source, "tool": tool,
                                 "calls": report["tool_call_counts"][tool],
                                 "proportion": round(report["tool_call_proportions"][tool], 4)})
        if len(reports) == 2:
            e, l = reports["expected"], reports["live"]
            for tool in inventory:
                comparison.append({"dataset": name, "tool": tool,
                                   "expected_calls": e["tool_call_counts"][tool],
                                   "live_calls": l["tool_call_counts"][tool],
                                   "expected_share": round(e["tool_call_proportions"][tool], 4),
                                   "live_share": round(l["tool_call_proportions"][tool], 4)})
        for row in summaries[-len(reports):]:
            print(f"{row['dataset']:<34} {row['source']:<9} diversity={row['diversity']}  "
                  f"tools={row['distinct_tools_used']}/{row['reference_tools']}  calls={row['recognized_calls']}")

    write_csv(args.output / "summary.csv", summaries)
    write_csv(args.output / "per_tool.csv", per_tool)
    write_csv(args.output / "comparison.csv", comparison)
    print(f"Reports written to {args.output}")


if __name__ == "__main__":
    main()
