"""Offline adapter tests and opt-in real-tool integration tests.

Run integrations with TAU2_BENCHMARK_ROOT=/path/to/tau2-bench and the tau2 extra.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.tau2.adapter import load_dataset
from validation.correctness_checker import CHECKS, run_experiment


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.domain = self.root / "data" / "tau2" / "domains" / "retail"
        self.domain.mkdir(parents=True)
        for name, value in {"tasks.json": [{"id": "a"}, {"id": "b"}],
                            "split_tasks.json": {"base": ["a", "b"], "test": ["b"]},
                            "db.json": {}}.items():
            (self.domain / name).write_text(json.dumps(value))
        (self.domain / "policy.md").write_text("Fixture policy")

    def test_roots_selection_provenance_and_raw_preservation(self):
        for root in (self.root, self.root / "data", self.root / "data" / "tau2"):
            result = load_dataset(root, split="test")
            self.assertEqual(result["task_ids"], ["b"])
            self.assertEqual(result["tasks"][0]["task"]["definition"], {"id": "b"})
            self.assertEqual(len(result["sources"]["sources"]["db.json"]["sha256"]), 64)
        self.assertEqual(load_dataset(self.root, limit=1)["task_ids"], ["a"])
        with self.assertRaises(ValueError):
            load_dataset(self.root, task_ids=["absent"])

    def test_malformed_records_retained_duplicate_ids_rejected(self):
        path = self.domain / "tasks.json"
        path.write_text(json.dumps([{"id": "a"}, {"id": ["bad"]}, "not a task"]))
        self.assertEqual(len(load_dataset(self.root)["tasks"]), 3)
        path.write_text(json.dumps([{"id": "a"}, {"id": "a"}]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_dataset(self.root)


BENCHMARK = os.environ.get("TAU2_BENCHMARK_ROOT")


@unittest.skipUnless(BENCHMARK, "Set TAU2_BENCHMARK_ROOT for real-tool integration tests")
class RealToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from loguru import logger
        logger.disable("tau2")
        from validation.tau2_corruptions import clean_retail_controls
        cls.dataset = load_dataset(BENCHMARK)
        cls.controls = clean_retail_controls(cls.dataset)

    def evaluate(self, payload):
        from evaluation.tau2 import evaluate
        return evaluate(payload)

    def test_full_dataset_load_and_empty_references(self):
        self.assertEqual(len(self.dataset["tasks"]), 114)
        empty = [e for e in self.dataset["tasks"] if not e["task"]["definition"]["evaluation_criteria"]["actions"]]
        self.assertEqual(len(empty), 2)
        for entry in empty:
            result = self.evaluate(entry["task"])
            self.assertEqual(result["checks"], dict(zip(CHECKS, (1, None, None, None))))
            self.assertEqual(result["outcome"]["status"], "not_evaluated")

    def test_controls_and_campaigns(self):
        from validation.tau2_corruptions import CAMPAIGNS, build_corruption_manifest
        subset = {**self.controls, "tasks": self.controls["tasks"][:2]}
        manifest = build_corruption_manifest(subset)
        result = run_experiment(manifest, self.evaluate, rates=(0, 1))
        self.assertTrue(result["passed"], [(r["kind"], r["passed"]) for r in result["campaigns"]])
        self.assertEqual({r["kind"] for r in result["campaigns"]}, set(CAMPAIGNS))
        self.assertEqual(result["baseline_false_positive_rate"], 0)
        self.assertTrue(all(r["outcome"]["status"] == "pass" for r in result["baseline_results"].values()))

    def test_independent_outcome_and_state_isolation(self):
        task = deepcopy(self.controls["tasks"][0]["task"])
        first = self.evaluate(task)
        self.assertEqual(first, self.evaluate(task))
        task["expected_final_state"][0]["value"] = "pending"
        second = self.evaluate(task)
        self.assertEqual(first["checks"], second["checks"])
        self.assertEqual(second["outcome"]["status"], "fail")
        self.assertEqual(first["outcome"]["status"], "pass")

    def test_strict_nested_types_and_duplicate_action_ids(self):
        task = deepcopy(self.controls["tasks"][0]["task"])
        actions = task["definition"]["evaluation_criteria"]["actions"]
        actions[0]["arguments"]["order_id"] = 123
        result = self.evaluate(task)
        self.assertEqual(result["checks"], dict(zip(CHECKS, (1, 0, None, None))))
        actions[0]["action_id"] = actions[1]["action_id"]
        self.assertEqual(self.evaluate(task)["checks"]["schema"], 0)
        task = deepcopy(self.controls["tasks"][0]["task"])
        action = task["definition"]["evaluation_criteria"]["actions"][0]
        action.update(name="return_delivered_order_items", arguments={"order_id": action["arguments"]["order_id"],
                      "item_ids": [123], "payment_method_id": "unused"})
        self.assertEqual(self.evaluate(task)["checks"]["signatures"], 0)

    def test_ownership_and_unknown_tools_do_not_execute(self):
        from evaluation.tau2.runtime import fresh_environment
        task = deepcopy(self.controls["tasks"][0]["task"])
        env, _, _ = fresh_environment(task["source"])
        order = env.tools.db.orders[task["definition"]["evaluation_criteria"]["actions"][0]["arguments"]["order_id"]]
        user = env.tools.db.users[order.user_id]
        other_payment = next(p for u in env.tools.db.users.values() for p in u.payment_methods if p not in user.payment_methods)
        task["definition"]["evaluation_criteria"]["actions"] = [{"action_id": "pay", "name": "modify_pending_order_payment",
             "arguments": {"order_id": order.order_id, "payment_method_id": other_payment}}]
        self.assertEqual(self.evaluate(task)["checks"]["references"], 0)
        task["definition"]["evaluation_criteria"]["actions"][0]["name"] = "unknown"
        with patch.object(type(env), "make_tool_call", side_effect=RuntimeError("must not execute")):
            self.assertEqual(self.evaluate(task)["checks"]["signatures"], 0)

    def test_initialization_history_applied_once_and_reads_executed(self):
        from evaluation.tau2.runtime import fresh_environment
        task = deepcopy(self.controls["tasks"][0]["task"])
        env, _, _ = fresh_environment(task["source"])
        read, cancel = task["definition"]["evaluation_criteria"]["actions"]
        task["definition"]["initial_state"] = {"message_history": [
            {"role": "assistant", "tool_calls": [{"id": "history-cancel", "name": cancel["name"],
                "arguments": cancel["arguments"], "requestor": "assistant"}]},
            {"role": "tool", "id": "history-cancel", "requestor": "assistant", "content":
                env.to_json_str(env.make_tool_call(cancel["name"], **cancel["arguments"]))}]}
        task["definition"]["evaluation_criteria"]["actions"] = [read]
        result = self.evaluate(task)
        self.assertEqual(result["checks"]["output_consistency"], 1)
        self.assertEqual([t["phase"] for t in result["trace"]], ["initial_history", "reference"])
        self.assertEqual(result["actions_executed"], 2)
        self.assertEqual(result["outcome"]["status"], "pass")
        task["definition"]["initial_state"]["message_history"][1]["id"] = "wrong"
        self.assertEqual(self.evaluate(task)["checks"]["schema"], 0)

    def test_initialization_updates_and_functions_applied_once(self):
        from evaluation.tau2.runtime import fresh_environment
        task = deepcopy(self.controls["tasks"][0]["task"])
        read, cancel = task["definition"]["evaluation_criteria"]["actions"]
        order_id = read["arguments"]["order_id"]
        env, _, _ = fresh_environment(task["source"])
        updated_order = env.tools.db.orders[order_id].model_dump(mode="json")
        updated_order["address"]["zip"] = "00000"
        task["definition"]["initial_state"] = {
            "initialization_data": {"agent_data": {"orders": {order_id: updated_order}}},
            "initialization_actions": [{"env_type": "assistant", "func_name": cancel["name"], "arguments": cancel["arguments"]}]}
        task["expected_final_state"].append({"path": ["agent", "orders", order_id, "address", "zip"], "value": "00000"})
        task["definition"]["evaluation_criteria"]["actions"] = [read]
        result = self.evaluate(task)
        self.assertEqual(result["checks"]["output_consistency"], 1)
        self.assertEqual(result["outcome"]["status"], "pass")
        self.assertEqual(len(result["trace"]), 1)
        task["definition"]["initial_state"]["initialization_actions"][0]["func_name"] = "unknown"
        self.assertEqual(self.evaluate(task)["checks"]["signatures"], 0)

    def test_repeated_item_modification_is_only_a_precondition_defect(self):
        from validation.tau2_corruptions import build_corruption_manifest
        from validation.correctness_checker import replace_at
        entry = next(e for e in self.dataset["tasks"] if e["id"] == "74")
        manifest = build_corruption_manifest({**self.dataset, "tasks": [entry]})
        mutation = next(m for m in manifest["mutations"] if m["kind"] == "broken_precondition")
        task = deepcopy(entry["task"])
        replace_at(task, mutation["path"], mutation["replacement"])
        self.assertEqual(self.evaluate(task)["checks"], mutation["expected_checks"])

    def test_replay_does_not_use_the_network(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network access forbidden")):
            result = self.evaluate(self.controls["tasks"][0]["task"])
        self.assertEqual(result["outcome"]["status"], "pass")

    def test_infrastructure_errors_and_source_mismatch_propagate(self):
        from evaluation.tau2.runtime import context
        task = deepcopy(self.controls["tasks"][0]["task"])
        context.cache_clear()
        task["source"]["sources"]["db.json"]["sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "Source hash mismatch"):
            self.evaluate(task)
        task = deepcopy(self.controls["tasks"][0]["task"])
        with patch("evaluation.tau2.evaluator.fresh_environment", side_effect=RuntimeError("broken evaluator")):
            with self.assertRaisesRegex(RuntimeError, "broken evaluator"):
                self.evaluate(task)

    def test_airline_and_telecom_smoke(self):
        for domain in ("airline", "telecom"):
            dataset = load_dataset(BENCHMARK, domain=domain, limit=1)
            result = self.evaluate(dataset["tasks"][0]["task"])
            self.assertEqual(set(result["checks"]), set(CHECKS))
            if domain == "telecom":
                self.assertTrue(any(t["requestor"] == "user" for t in result["trace"]))

    def test_telecom_initial_updates_preserve_distinct_agent_and_user_databases(self):
        task = load_dataset(BENCHMARK, domain="telecom", limit=1)["tasks"][0]["task"]
        baseline = self.evaluate(task)
        task["definition"]["initial_state"]["initialization_data"] = {"agent_data": {}, "user_data": {}}
        result = self.evaluate(task)
        self.assertEqual(result["checks"], baseline["checks"])
        self.assertEqual(result["final_state_sha256"], baseline["final_state_sha256"])
        self.assertEqual(result["outcome"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
