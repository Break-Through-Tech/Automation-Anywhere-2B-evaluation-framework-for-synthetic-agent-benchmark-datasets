"""Separate workflow for existing half-duplex agent runs; never generate runs."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from .adapter import fingerprint, load_dataset
from .evaluator import _history_actions, evaluate
from .runtime import dependencies
from validation.reporting import evaluate_dataset, terminal_summary, write_error, write_reports


def load_recorded_dataset(path, dataset, allow_task_drift=False, limit=None):
    """Preserve embedded expectations; reject changed tasks before any replay.

    Existing result artifacts do not necessarily identify their original DB
    snapshot. This workflow explicitly evaluates against the supplied snapshot,
    and does not claim to reproduce historical leaderboard rewards.
    """
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("limit must be a positive integer")
    dependencies()
    from pydantic import TypeAdapter
    from tau2.data_model.message import Message
    from tau2.data_model.tasks import Task
    path = Path(path).resolve()
    document = json.loads(path.read_text())
    if not isinstance(document, dict) or not isinstance(document.get("tasks"), list) or not isinstance(document.get("simulations"), list):
        raise ValueError("Recorded results must contain tasks and simulations lists")
    definitions = {}
    for task in document["tasks"]:
        key = task["id"]
        if key in definitions:
            raise ValueError(f"Duplicate embedded task ID: {key}")
        definitions[key] = task
    current = {entry["id"]: entry["task"] for entry in dataset["tasks"]}
    tasks, drift, seen = [], [], set()
    for simulation in document["simulations"]:
        task_id, key = simulation["task_id"], simulation["id"]
        if task_id not in current:
            continue
        if not isinstance(key, str) or key in seen:
            raise ValueError("Simulation IDs must be unique strings")
        seen.add(key)
        if task_id not in definitions:
            raise ValueError(f"No embedded task definition for {task_id}")
        original = definitions[task_id]
        embedded_model = Task.model_validate(original).model_dump(mode="json")
        selected_model = Task.model_validate(current[task_id]["definition"]).model_dump(mode="json")
        if embedded_model != selected_model:
            drift.append(task_id)
            if not allow_task_drift:
                raise ValueError(f"Recorded task {task_id} differs from supplied benchmark tasks. "
                                 "Use matching benchmark data or explicitly --allow-task-drift to replay embedded tasks on the supplied snapshot.")
        if "ticks" in simulation and simulation["ticks"]:
            raise ValueError("Full-duplex tick trajectories are not supported; provide half-duplex messages")
        messages = TypeAdapter(list[Message]).validate_json(json.dumps(simulation["messages"]), strict=True)
        # Full trajectories contain the initial message-history prefix. The
        # evaluator replays that prefix independently exactly once.
        initial = embedded_model.get("initial_state") or {}
        prefix = initial.get("message_history") or []
        if prefix:
            normalized = [m.model_dump(mode="json") for m in messages[:len(prefix)]]
            if normalized != prefix:
                raise ValueError("Recorded trajectory does not start with the embedded initialization history")
            candidate_messages = messages[len(prefix):]
        else:
            candidate_messages = messages
        actions, outputs = [], {}
        for action, output in _history_actions(candidate_messages):
            actions.append(action)
            outputs[action["action_id"]] = output
        tasks.append({"id": key, "task": {"source": deepcopy(current[task_id]["source"]),
                      "definition": deepcopy(original), "candidate_actions": actions,
                      "expected_outputs": outputs, "subject": "recorded_agent_run",
                      "assistant_messages": [m.content for m in messages if m.role == "assistant" and isinstance(m.content, str)],
                      "termination_reason": simulation.get("termination_reason"),
                      "recording": {"task_id": task_id, "trial": simulation.get("trial"), "seed": simulation.get("seed")}}})
        if limit is not None and len(tasks) >= limit:
            break
    if not tasks:
        raise ValueError("No recorded simulations match selected tasks")
    return {"dataset": dataset["dataset"] + "/recorded-runs", "subject": "recorded_agent_runs",
            "sources": dataset["sources"], "recording": {"path": str(path), "sha256": fingerprint(path)},
            "task_drift": sorted(set(drift)), "snapshot_provenance": "Supplied snapshot; historical snapshot identity unverified",
            "tasks": tasks, "mutations": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--domain", choices=("retail", "airline", "telecom"), default="retail")
    parser.add_argument("--split", default="base")
    parser.add_argument("--task-ids", nargs="+")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--allow-task-drift", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("output/tau2-recorded-correctness"))
    args = parser.parse_args()
    try:
        from loguru import logger
        logger.disable("tau2")
        if args.limit is not None and args.limit < 1:
            raise ValueError("limit must be positive")
        dataset = load_dataset(args.benchmark_root, args.domain, args.split, args.task_ids)
        manifest = load_recorded_dataset(args.results, dataset, args.allow_task_drift, args.limit)
        report = evaluate_dataset(manifest, evaluate)
        report["evaluator"] = "evaluation.tau2:evaluate (recorded-run workflow)"
        write_reports(report, manifest, args.output)
        print(terminal_summary(report, args.output))
        print("Agent-run results are separate from dataset-quality scores. Historical snapshot identity is unverified.")
        return 0
    except Exception as error:
        try:
            path = write_error(error, args.output)
        except OSError:
            path = "unavailable (output directory is not writable)"
        parser.exit(2, f"Evaluation error: {type(error).__name__}: {error}\nDiagnostics: {path}\n")


if __name__ == "__main__":
    raise SystemExit(main())
