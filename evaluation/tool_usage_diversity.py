"""Tool usage entropy and perturbations for a fixed tool inventory."""

from collections import Counter
import math
from typing import Any


def calculate_diversity(call_counts: dict[str, int], reference_tools: list[str]) -> dict[str, Any]:
    """Calculate entropy and report counts for a fixed reference inventory."""
    tools = sorted(set(reference_tools))
    if not tools:
        raise ValueError("Configure at least one reference tool.")
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in call_counts.values()):
        raise ValueError("Tool counts must be non-negative integers.")

    counts = {name: call_counts.get(name, 0) for name in tools}
    unknown = {name: count for name, count in sorted(call_counts.items())
               if name not in tools and count > 0}
    total = sum(counts.values())
    entropy = -sum((count / total) * math.log(count / total)
                   for count in counts.values() if count) if total else None
    score = (0.0 if len(tools) == 1 else max(0.0, min(1.0, entropy / math.log(len(tools))))) if total else None
    used = sum(count > 0 for count in counts.values())
    balance = (0.0 if used <= 1 else entropy / math.log(used)) if total else None

    return {
        "total_tool_calls": total + sum(unknown.values()),
        "recognized_tool_calls": total,
        "unknown_tool_calls": sum(unknown.values()),
        "unknown_tool_call_counts": unknown,
        "distinct_tools_used": used,
        "reference_tool_count": len(tools),
        "tool_call_counts": counts,
        "tool_call_proportions": {name: count / total if total else 0.0
                                   for name, count in counts.items()},
        "raw_shannon_entropy": entropy,
        "tool_balance": balance,
        "normalized_tool_usage_diversity": score,
    }


def validate_perturbations(report: dict[str, Any], reference_tools: list[str]) -> dict[str, Any]:
    """Compare baseline with global-single-tool and per-task-single-tool subsets."""
    calls = [name for task in report["task_calls"] for name in task["calls"]
             if name in reference_tools]
    baseline = report["normalized_tool_usage_diversity"]

    def compare(selected_calls: list[str]) -> dict[str, Any]:
        metrics = calculate_diversity(dict(Counter(selected_calls)), reference_tools)
        score = metrics["normalized_tool_usage_diversity"]
        return {
            "tool_call_count": metrics["recognized_tool_calls"],
            "tools_represented": sorted(set(selected_calls)),
            "normalized_tool_usage_diversity": score,
            "absolute_score_change": abs(baseline - score) if baseline is not None and score is not None else None,
            "relative_score_change": (score - baseline) / baseline
                if baseline not in (None, 0) and score is not None else None,
            "expected_decrease": baseline > score + 1e-12
                if baseline is not None and score is not None else None,
        }

    selected = max(Counter(calls), key=lambda name: (Counter(calls)[name], name)) if calls else None
    strict = compare([name for name in calls if name == selected]) if selected else compare([])
    strict.update({"selected_tool": selected, "passed": strict["normalized_tool_usage_diversity"] == 0.0
                   if selected else None})
    single_tool_tasks = [task["calls"] for task in report["task_calls"]
                         if len(set(task["calls"]) & set(reference_tools)) == 1]
    task_level = compare([name for task in single_tool_tasks for name in task
                          if name in reference_tools])
    task_level.update({"task_count": len(single_tool_tasks), "supported": bool(single_tool_tasks)})
    return {"baseline_diversity": baseline, "baseline_tools_represented": sorted(set(calls)),
            "strict_single_tool": strict, "task_level_single_tool_subset": task_level}
