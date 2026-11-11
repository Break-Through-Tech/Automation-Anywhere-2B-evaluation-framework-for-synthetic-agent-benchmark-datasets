"""Operational correctness of reference tasks; never an LLM judge."""

from copy import deepcopy
import hashlib
import inspect
import json

from validation.correctness_checker import CHECKS
from .references import ReferenceFailure, validate_references
from .runtime import dependencies, differences, fresh_environment, state


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _schema(definition):
    from pydantic import ValidationError
    from tau2.data_model.tasks import Task
    try:
        task = Task.model_validate_json(json.dumps(definition), strict=True)
    except ValidationError as error:
        return None, [{"path": list(e["loc"]), "message": e["msg"]}
                      for e in error.errors(include_url=False, include_context=False)]
    actions = (definition.get("evaluation_criteria") or {}).get("actions") or []
    ids = [a["action_id"] for a in actions]
    if not task.id.strip() or any(not value.strip() for value in ids):
        return None, [{"path": ["id"], "message": "Task and action IDs must be nonempty"}]
    if len(ids) != len(set(ids)):
        return None, [{"path": ["evaluation_criteria", "actions"],
                       "message": "Action IDs must be unique"}]
    return task, []


def _history_actions(messages):
    """Preserve order and pair every initial-history call with its tool result."""
    index = 0
    while index < len(messages):
        message = messages[index]
        if message.role == "tool":
            raise ValueError("Unexpected tool result in initialization history")
        index += 1
        for call in getattr(message, "tool_calls", None) or []:
            if call.requestor != message.role:
                raise ValueError("Tool call requestor differs from message role")
            if index >= len(messages) or messages[index].role != "tool" or messages[index].id != call.id:
                raise ValueError("Initialization tool calls must have matching ordered results")
            result = messages[index]
            if result.requestor != call.requestor:
                raise ValueError("Initialization tool result requestor differs from call")
            yield {"action_id": call.id, "requestor": call.requestor,
                   "name": call.name, "arguments": call.arguments}, result.content
            index += 1


def _outcome(payload, parsed, env, replay_complete, current):
    assertions = payload.get("expected_final_state", [])
    criteria = parsed.evaluation_criteria
    env_assertions = criteria.env_assertions if criteria else None
    uncovered = []
    if criteria and criteria.communicate_info:
        uncovered.append("Reference actions contain no agent dialogue to check communication requirements")
    if criteria and criteria.nl_assertions:
        uncovered.append("Natural-language requirements require independent executable assertions; no LLM judge is used")
    if not replay_complete or not (assertions or env_assertions):
        return {"status": "not_evaluated", "reason": "Replay blocked" if not replay_complete else
                "No independent executable outcome expectations", "uncovered": uncovered, "assertions": []}
    results = []
    for assertion in assertions:
        if (not isinstance(assertion, dict) or not isinstance(assertion.get("path"), list)
                or not assertion["path"] or "value" not in assertion):
            raise ValueError("Outcome assertions require nonempty path and value")
        actual = current
        try:
            for part in assertion["path"]:
                actual = actual[part]
        except (KeyError, IndexError, TypeError):
            results.append({**assertion, "met": False, "reason": "Expected state path absent"})
        else:
            results.append({**assertion, "actual": actual,
                            "met": type(actual) is type(assertion["value"]) and actual == assertion["value"]})
    for assertion in env_assertions or []:
        kit = env.tools if assertion.env_type == "assistant" else env.user_tools
        if kit is None or not assertion.func_name.startswith("assert_") or not callable(getattr(kit, assertion.func_name, None)):
            raise ValueError(f"Unsupported outcome assertion: {assertion.func_name}")
        met = env.run_env_assertion(assertion, raise_assertion_error=False)
        results.append({"assertion": assertion.model_dump(mode="json"), "met": bool(met)})
    return {"status": "pass" if all(r["met"] for r in results) else "fail",
            "assertions": results, "uncovered": uncovered,
            "reason": "Independent executable assertions only; prose task success is not established"}


def evaluate(payload):
    """Return binary operational checks, action evidence, coverage, and outcome.

    All signatures are checked before stateful replay. Replay stops on the first
    reference or execution failure. Blocked checks are unavailable, never passes.
    Expected domain ValueError/AssertionError failures are defects; other Python
    exceptions propagate as experiment errors.
    """
    dependencies()
    definition = deepcopy(payload["definition"])
    if "candidate_actions" in payload and isinstance(definition, dict):
        if definition.get("evaluation_criteria") is None:
            definition["evaluation_criteria"] = {}
        if isinstance(definition["evaluation_criteria"], dict):
            definition["evaluation_criteria"]["actions"] = payload["candidate_actions"]
    parsed, problems = _schema(definition)
    checks = dict.fromkeys(CHECKS)
    checks["schema"] = int(not problems)
    result = {"checks": checks, "evidence": {c: [] for c in CHECKS}, "coverage": {},
              "trace": [], "outcome": {"status": "not_evaluated", "reason": "Replay blocked"},
              "fully_evaluated": False}
    result["evidence"]["schema"] = problems

    def unavailable(reason, categories):
        for category in categories:
            result["coverage"][category] = {"status": "blocked", "reason": reason}

    if parsed is None:
        unavailable("Task schema invalid", CHECKS[1:])
        return result
    env, validators, metadata = fresh_environment(payload["source"])
    result["runtime"] = metadata
    initial = parsed.initial_state
    try:
        history = list(_history_actions(initial.message_history or [])) if initial else []
    except ValueError as error:
        checks["schema"] = 0
        result["evidence"]["schema"].append({"path": ["initial_state", "message_history"], "message": str(error)})
        unavailable("Initialization history invalid", CHECKS[1:])
        return result
    raw_actions = deepcopy((definition.get("evaluation_criteria") or {}).get("actions") or [])
    actions = [(a, output, "initial_history") for a, output in history]
    expected_outputs = payload.get("expected_outputs", {})
    actions += [(a, expected_outputs.get(a["action_id"]), "reference") for a in raw_actions]
    all_ids = [a["action_id"] for a, _, _ in actions]
    if len(all_ids) != len(set(all_ids)):
        checks["schema"] = 0
        result["evidence"]["schema"].append({"message": "Action IDs overlap between initial history and reference/candidate actions"})
        unavailable("Duplicate action IDs", CHECKS[1:])
        return result
    if actions:
        checks["signatures"] = 1
    for action, _, phase in actions:
        validator = validators.get(action.get("requestor", "assistant"), {}).get(action["name"])
        errors = (["Unknown tool for requestor"] if validator is None else
                  [e.message for e in validator.iter_errors(action["arguments"])])
        if errors:
            checks["signatures"] = 0
            result["evidence"]["signatures"].append({"action_id": action["action_id"],
                 "action": action["name"], "phase": phase, "message": "; ".join(errors)})
    if checks["signatures"] == 0:
        unavailable("Invalid tool signature prevents replay", ("references", "output_consistency"))
        return result
    for action in (initial.initialization_actions or []) if initial else []:
        kit = env.tools if action.env_type == "assistant" else env.user_tools
        function = getattr(kit, action.func_name, None) if kit else None
        try:
            if not callable(function):
                raise TypeError(f"Unknown initialization function: {action.func_name}")
            inspect.signature(function).bind(**action.arguments)
        except TypeError as error:
            checks["signatures"] = 0
            result["evidence"]["signatures"].append({"phase": "initialization", "action": action.func_name, "message": str(error)})
            unavailable("Invalid initialization function signature", ("references", "output_consistency"))
            return result
    # Apply data updates once, then initialization functions once, then history once.
    try:
        updates = initial.initialization_data if initial else None
        if updates is not None:
            if updates.agent_data is not None:
                env.tools.update_db(updates.agent_data)
            if updates.user_data is not None:
                if env.user_tools is None:
                    raise ValueError("User initialization data provided for a domain without user tools")
                env.user_tools.update_db(updates.user_data)
        # Telecom has different agent/user DB models. Do not use set_state's
        # shared-DB reassignment when applying these independent updates.
        env.sync_tools()
        for action in (initial.initialization_actions or []) if initial else []:
            env.run_env_function_calls([action])
    except (ValueError, AssertionError) as error:
        checks["output_consistency"] = 0
        result["evidence"]["output_consistency"].append({"phase": "initialization", "message": str(error)})
        unavailable("Initialization failed", ("references",))
        return result
    before = state(env)
    bindings, complete = 0, True
    for index, (action, expected, phase) in enumerate(actions):
        trace = {"index": index, "phase": phase, "action_id": action["action_id"],
                 "action": action["name"], "requestor": action.get("requestor", "assistant")}
        result["trace"].append(trace)
        try:
            bindings += validate_references(payload["source"]["domain"], env, action)
        except ReferenceFailure as error:
            checks["references"] = 0
            result["evidence"]["references"].append({**trace, "message": str(error)})
            trace["status"] = "invalid_reference"
            unavailable("Entity reference invalid", ("output_consistency",))
            complete = False
            break
        try:
            response = env.make_tool_call(action["name"], requestor=trace["requestor"], **action["arguments"])
            env.sync_tools()
        except (ValueError, AssertionError) as error:
            checks["output_consistency"] = 0
            result["evidence"]["output_consistency"].append({**trace, "message": str(error)})
            trace["status"] = "execution_failed"
            complete = False
            if index + 1 < len(actions):
                unavailable("Replay failed before remaining references could be checked", ("references",))
            break
        serialized = env.to_json_str(response)
        trace.update(status="executed", output_sha256=_hash(serialized), output_preview=serialized[:400])
        if expected is not None:
            try:
                actual = json.loads(serialized)
            except json.JSONDecodeError:
                actual = serialized
            try:
                expected_value = json.loads(expected) if isinstance(expected, str) else expected
            except json.JSONDecodeError:
                expected_value = expected
            if actual != expected_value:
                checks["output_consistency"] = 0
                trace["status"] = "output_mismatch"
                result["evidence"]["output_consistency"].append({**trace,
                    "message": "Actual output differs from independently recorded expected output"})
                complete = False
                if index + 1 < len(actions):
                    unavailable("Output mismatch prevented checking remaining references", ("references",))
                break
    if checks["references"] is None and bindings and result["coverage"].get("references", {}).get("status") != "blocked":
        checks["references"] = 1
    if complete and actions:
        checks["output_consistency"] = 1
    after = state(env)
    result["state_changes"] = differences(before, after)
    result["final_state_sha256"] = _hash(after)
    result["outcome"] = _outcome(payload, parsed, env, complete, after)
    if payload.get("subject") == "recorded_agent_run":
        result["outcome"] = recorded_outcome(payload, result, complete)
    for category, value in checks.items():
        result["coverage"].setdefault(category, {
            "status": "evaluated" if value is not None else "not_applicable",
            "reason": ("No mapped entity arguments" if category == "references" else "No calls")
                      if value is None else "Check performed"})
    result["coverage"]["references"]["bindings_checked"] = bindings
    result["fully_evaluated"] = all(v is not None for v in checks.values())
    result["replay_complete"] = complete
    result["actions_executed"] = sum(t["status"] == "executed" for t in result["trace"])
    return result


def recorded_outcome(payload, result, complete):
    """Compare a candidate replay against a separate immutable reference target.

    This is intentionally not the official leaderboard reward: unsupported
    semantic criteria remain uncovered instead of invoking an LLM.
    """
    if not complete:
        return {"status": "not_evaluated", "reason": "Candidate replay blocked"}
    criteria = payload["definition"].get("evaluation_criteria")
    if criteria is None:
        return {"status": "not_evaluated", "reason": "No independent outcome criteria in the embedded task"}
    basis = criteria.get("reward_basis", ["DB", "COMMUNICATE"])
    components, uncovered = {}, []
    if "DB" in basis:
        if criteria.get("actions") is None:
            uncovered.append("No explicit reference actions from which to derive a DB target")
        else:
            reference = evaluate({"source": payload["source"], "definition": payload["definition"]})
            if not reference.get("replay_complete"):
                uncovered.append("Reference target could not be replayed")
            else:
                components["DB"] = reference["final_state_sha256"] == result["final_state_sha256"]
    if "COMMUNICATE" in basis:
        messages = payload.get("assistant_messages", [])
        components["COMMUNICATE"] = all(any(value.lower() in message.lower() for message in messages)
                                        for value in criteria.get("communicate_info") or [])
    if "ENV_ASSERTION" in basis:
        if result["outcome"]["status"] != "not_evaluated":
            components["ENV_ASSERTION"] = result["outcome"]["status"] == "pass"
        else:
            uncovered.append("No executable environment assertions")
    for criterion in basis:
        if criterion not in ("DB", "COMMUNICATE", "ENV_ASSERTION"):
            uncovered.append(f"Reward criterion {criterion} is not evaluated in this offline workflow")
    if payload.get("termination_reason") not in ("agent_stop", "user_stop"):
        components["normal_termination"] = False
    status = "fail" if any(not v for v in components.values()) else ("not_evaluated" if uncovered or not components else "pass")
    return {"status": status, "components": components, "uncovered": uncovered,
            "reason": "Candidate compared with separate reference target on the supplied snapshot; not an official leaderboard regrade"}
