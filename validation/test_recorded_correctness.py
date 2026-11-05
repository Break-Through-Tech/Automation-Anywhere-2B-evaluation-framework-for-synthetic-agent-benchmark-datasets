from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest


@unittest.skipUnless(os.environ.get("TAU2_BENCHMARK_ROOT"), "Set TAU2_BENCHMARK_ROOT for recorded-run integration tests")
class RecordedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from loguru import logger
        logger.disable("tau2")
        from evaluation.tau2 import load_dataset
        from validation.tau2_corruptions import clean_retail_controls
        cls.dataset = clean_retail_controls(load_dataset(os.environ["TAU2_BENCHMARK_ROOT"]))

    def recording(self):
        from evaluation.tau2.runtime import fresh_environment
        task = self.dataset["tasks"][0]["task"]
        env, _, _ = fresh_environment(task["source"])
        messages = []
        for action in task["definition"]["evaluation_criteria"]["actions"]:
            messages.append({"role": "assistant", "tool_calls": [{"id": action["action_id"],
                 "name": action["name"], "arguments": action["arguments"]}]})
            messages.append({"role": "tool", "id": action["action_id"], "requestor": "assistant",
                             "content": env.to_json_str(env.make_tool_call(action["name"], **action["arguments"]))})
        return {"tasks": [deepcopy(task["definition"])], "simulations": [{"id": "run-1",
                "task_id": task["definition"]["id"], "messages": messages, "termination_reason": "agent_stop"}]}

    def load(self, document, **kwargs):
        from evaluation.tau2.recorded import load_recorded_dataset
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recording.json"
            path.write_text(json.dumps(document))
            return load_recorded_dataset(path, self.dataset, **kwargs)

    def test_candidate_and_reference_targets_are_separate(self):
        from evaluation.tau2 import evaluate
        manifest = self.load(self.recording())
        payload = manifest["tasks"][0]["task"]
        self.assertEqual(evaluate(payload)["outcome"]["status"], "pass")
        payload["candidate_actions"] = payload["candidate_actions"][:1]
        result = evaluate(payload)
        self.assertEqual(result["checks"]["output_consistency"], 1)
        self.assertEqual(result["outcome"]["status"], "fail")
        self.assertFalse(result["outcome"]["components"]["DB"])

    def test_task_drift_rejected_and_explicit_override_preserves_embedded_task(self):
        recording = self.recording()
        recording["tasks"][0]["user_scenario"]["instructions"] = "Changed instructions"
        with self.assertRaisesRegex(ValueError, "differs"):
            self.load(recording)
        manifest = self.load(recording, allow_task_drift=True)
        self.assertTrue(manifest["task_drift"])
        self.assertEqual(manifest["tasks"][0]["task"]["definition"]["user_scenario"]["instructions"], "Changed instructions")

    def test_recorded_output_mismatch_and_abnormal_termination(self):
        from evaluation.tau2 import evaluate
        recording = self.recording()
        recording["simulations"][0]["messages"][1]["content"] = '"incorrect output"'
        payload = self.load(recording)["tasks"][0]["task"]
        self.assertEqual(evaluate(payload)["checks"]["output_consistency"], 0)
        recording = self.recording()
        recording["simulations"][0]["termination_reason"] = "max_steps"
        payload = self.load(recording)["tasks"][0]["task"]
        self.assertEqual(evaluate(payload)["outcome"]["status"], "fail")

    def test_mismatched_tool_result_ids_rejected(self):
        recording = self.recording()
        recording["simulations"][0]["messages"][1]["id"] = "other-call"
        with self.assertRaisesRegex(ValueError, "matching ordered"):
            self.load(recording)

    def test_missing_outcome_criteria_do_not_invent_an_initial_state_target(self):
        from evaluation.tau2 import evaluate
        recording = self.recording()
        recording["tasks"][0]["evaluation_criteria"] = None
        payload = self.load(recording, allow_task_drift=True)["tasks"][0]["task"]
        result = evaluate(payload)
        self.assertEqual(result["checks"]["output_consistency"], 1)
        self.assertEqual(result["outcome"]["status"], "not_evaluated")
