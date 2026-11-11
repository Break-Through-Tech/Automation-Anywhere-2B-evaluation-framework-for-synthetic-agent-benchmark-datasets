"""Offline tests: static τ-bench inputs, shared scoring, and isolated resumable reports."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

try:
    from . import llm_judge as judge
    from .tau_adapter import (BENCHMARK_COMMIT, DEFAULT_OUTPUT_DIR, DEFAULT_TAU2_DIR,
                              TauBenchAdapter, select_initial_records)
except ImportError:
    import llm_judge as judge
    from tau_adapter import (BENCHMARK_COMMIT, DEFAULT_OUTPUT_DIR, DEFAULT_TAU2_DIR,
                             TauBenchAdapter, select_initial_records)


class StaticInputsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / "data/tau2/domains/retail"
        self.src = self.root / "src/tau2/domains/retail"
        self.data.mkdir(parents=True)
        self.src.mkdir(parents=True)
        self.task = {
            "id": "task-1", "user_scenario": {"instructions": {"reason_for_call": "Order O1"}},
            "evaluation_criteria": {"actions": [{"name": "lookup", "arguments": {"order_id": "O1"}}]},
            "initial_state": None,
        }
        self.write("tasks.json", [self.task])
        self.write("split_tasks.json", {"test": ["task-1"]})
        self.write("db.json", {"orders": {"O1": {"user_id": "U1"}}, "users": {"U1": {"name": "Ada"}}})
        (self.data / "policy.md").write_text("Verify the customer before changing an order.")
        (self.src / "tools.py").write_text('''
raise AssertionError("Benchmark code must never execute")
class RetailTools:
    @is_tool(ToolType.READ)
    def lookup(self, order_id: str) -> dict:
        """Read an order."""
        return self._helper(order_id)
    def _helper(self, order_id):
        return self.db.orders[order_id]
''')
        for name in ("data_model.py", "utils.py", "environment.py"):
            (self.src / name).write_text("raise AssertionError('Must not import benchmark code')")
        for name in ("data_model/tasks.py", "environment/toolkit.py", "environment/db.py"):
            path = self.root / "src/tau2" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Source fixture")
        mock_git = patch(f"{TauBenchAdapter.__module__}._git", side_effect=self.git)
        mock_git.start()
        self.addCleanup(mock_git.stop)

    @staticmethod
    def git(root, *args):
        return "" if args[0] == "status" else BENCHMARK_COMMIT

    def write(self, name, value):
        (self.data / name).write_text(json.dumps(value))

    def adapter(self):
        return TauBenchAdapter(self.root, domain="retail", split="test")

    def test_static_mapping_preserves_raw_criteria_and_initial_evidence(self):
        a = self.adapter()
        payload = a.payload(*a.tasks[0])
        self.assertEqual(payload["task"]["test_case_id"], "task-1")
        self.assertEqual(payload["task"]["evaluation_criteria"], self.task["evaluation_criteria"])
        self.assertEqual(payload["evaluation_criteria"]["reward_basis"], ["DB", "COMMUNICATE"])
        self.assertEqual(payload["initial_state"]["default_agent_database"]["records"]["users"], {"U1": {"name": "Ada"}})
        methods = payload["available_tools"]["assistant"]["referenced_implementations"]
        self.assertEqual(set(methods), {"lookup", "_helper"})
        self.assertEqual(set(payload["available_tools"]["assistant"]["available_tools"]), {"lookup"})
        self.assertTrue(all(len(v) == 64 for v in a.manifest()["source_sha256"].values()))

    def test_duplicate_ids_and_missing_split_records_fail(self):
        self.write("tasks.json", [self.task, self.task])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.adapter()
        self.write("tasks.json", [self.task])
        self.write("split_tasks.json", {"test": ["absent"]})
        with self.assertRaisesRegex(ValueError, "missing tasks"):
            self.adapter()

    def test_missing_sources_and_missing_instructions_fail(self):
        (self.data / "policy.md").unlink()
        with self.assertRaisesRegex(ValueError, "Cannot read required"):
            self.adapter()
        (self.data / "policy.md").write_text("Policy")
        self.task["user_scenario"] = {}
        self.write("tasks.json", [self.task])
        with self.assertRaisesRegex(ValueError, "Missing instructions"):
            self.adapter()

    def test_pinned_version_dirty_checkout_and_invalid_selection_fail(self):
        with patch(f"{TauBenchAdapter.__module__}._git", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "Expected v1.0.1"):
                self.adapter()
        with patch(f"{TauBenchAdapter.__module__}._git", side_effect=lambda root, *args: " M tasks.json" if args[0] == "status" else BENCHMARK_COMMIT):
            with self.assertRaisesRegex(ValueError, "tracked modifications"):
                self.adapter()
        for kwargs in ({"domain": "unknown"}, {"limit": 0}, {"split": "absent"}):
            with self.assertRaises(ValueError):
                TauBenchAdapter(self.root, **kwargs)

    def test_identity_selection_is_bounded_and_follows_outgoing_ids(self):
        database = {"orders": {"O1": {"user_id": "U1"}, "O10": {"user_id": "U2"}},
                    "users": {"U1": {"name": {"first_name": "Ada", "last_name": "Lovelace"}},
                              "U2": {"name": {"first_name": "Unrelated", "last_name": "Person"}}}}
        result = select_initial_records(database, {"instructions": "Read O1"})
        self.assertEqual(set(result["records"]["orders"]), {"O1"})
        self.assertEqual(set(result["records"]["users"]), {"U1"})
        self.assertEqual(select_initial_records(database, {"name": "Ada Lovelace"})["selected_counts"]["users"], 1)
        result["records"]["orders"]["O1"]["user_id"] = "changed"
        self.assertEqual(database["orders"]["O1"]["user_id"], "U1")


class SharedJudgeTests(unittest.TestCase):
    def test_only_dataset_wording_changes_in_tau_prompt(self):
        self.assertEqual(judge.PROMPT_VERSION, "1.0")
        self.assertEqual(judge.TAU_SYSTEM_PROMPT, judge.SYSTEM_PROMPT.replace("SYNTHETIC benchmark TASK DATA", "benchmark TASK DATA", 1))
        self.assertNotEqual(judge.TAU_PROMPT_VERSION, judge.PROMPT_VERSION)

    def test_request_options_and_weighting_unchanged(self):
        result = judge.JudgeResult(**{
            d: {"score": score, "explanation": "Specific evidence in task", "evidence": ["task.field"]}
            for d, score in zip(judge.DIMENSIONS, (1.0, 0.5, 0.0, 1.0))
        })
        client = MagicMock()
        client.beta.chat.completions.parse.return_value.choices[0].message.parsed = result
        payload = {"domain": "retail", "task": {"test_case_id": "1", "title": "Title"}}
        self.assertEqual(judge.judge_task(client, "gpt-6-luna", payload), result)
        request = client.beta.chat.completions.parse.call_args.kwargs
        self.assertEqual(set(request), {"model", "messages", "response_format"})
        self.assertEqual(request["messages"][0]["content"], judge.SYSTEM_PROMPT)
        record = judge.make_record(payload, result, "gpt-6-luna")
        self.assertEqual(record["task_score"], 0.625)
        self.assertEqual(record["prompt_version"], "1.0")


@unittest.skipUnless(DEFAULT_TAU2_DIR.is_dir(), "Pinned local τ-bench checkout not available")
class PinnedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = TauBenchAdapter()

    def cli(self, *args):
        with patch("sys.argv", ["llm_judge.py", *args]), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return judge.main()

    def judgment(self):
        return judge.JudgeResult(**{d: {"score": 0.5, "explanation": "Offline mocked judgment", "evidence": ["task.user_scenario"]} for d in judge.DIMENSIONS})

    def test_official_base_selection_and_payloads_for_each_domain(self):
        self.assertEqual(self.adapter.selected_counts, {"airline": 50, "retail": 114, "telecom": 114})
        self.assertEqual(len(self.adapter.tasks), 278)
        self.assertEqual(len({(d, t["id"]) for d, t in self.adapter.tasks}), 278)
        for domain in self.adapter.selected_counts:
            item = next(x for x in self.adapter.tasks if x[0] == domain)
            payload = self.adapter.payload(*item)
            self.assertTrue(payload["policy"])
            self.assertTrue(payload["evaluation_criteria"]["reward_basis"])
            self.assertTrue(payload["available_tools"]["assistant"]["available_tools"])
            self.assertFalse(payload["available_tools"]["assistant"]["unresolved_references"])
            self.assertTrue(any(payload["initial_state"]["default_agent_database"]["records"].values()))
            if domain == "airline":
                self.assertIn("EHGLP3", payload["initial_state"]["default_agent_database"]["records"]["reservations"])
            if domain == "telecom":
                self.assertEqual(len(payload["policy"]), 2)
                self.assertTrue(payload["initial_state"]["default_user_database"]["device"])
                self.assertTrue(payload["initial_state"]["task_directives"]["initialization_actions"])
                implementations = payload["available_tools"]["user"]["referenced_implementations"]
                self.assertIn("assert_internet_speed", implementations)
                self.assertIn("set_user_info", implementations)

    def test_dry_run_has_no_api_calls_or_output_writes(self):
        with tempfile.TemporaryDirectory() as tmp, patch("openai.OpenAI", side_effect=AssertionError("No API")):
            out = Path(tmp) / "not_created"
            self.cli("--dataset", "tau2", "--domain", "telecom", "--limit", "1", "--dry-run", "--output-dir", str(out))
            self.assertFalse(out.exists())

    def test_mocked_three_domain_pilot_reports_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"OPENAI_API_KEY": "offline-test-placeholder"}), patch("openai.OpenAI"), patch.object(judge, "judge_task", return_value=self.judgment()) as mocked:
            for domain in ("airline", "retail", "telecom"):
                args = ("--dataset", "tau2", "--domain", domain, "--limit", "1", "--model", "gpt-6-luna", "--output-dir", tmp, "--resume")
                self.cli(*args)
                self.cli(*args)
            self.assertEqual(mocked.call_count, 3)
            self.assertEqual(mocked.call_args.kwargs["system_prompt"], judge.TAU_SYSTEM_PROMPT)
            records = json.loads((Path(tmp) / "judge_details.json").read_text())
            metadata = json.loads((Path(tmp) / "run_metadata.json").read_text())
            self.assertEqual(len(records), 3)
            self.assertEqual(len(metadata["task_selection"]), 3)
            self.assertTrue(all(r["benchmark_commit"] == BENCHMARK_COMMIT and r["task_score"] == 0.5 for r in records))
            self.assertEqual((Path(tmp) / "task_scores.csv").read_text().splitlines()[0], "domain,task_id,task_score," + ",".join(judge.DIMENSIONS) + ",uncertain_count")
            self.assertIn("OVERALL,3,0.5,12,0", (Path(tmp) / "domain_scores.csv").read_text())
            for field, value in (("benchmark_commit", "wrong"), ("model", "other-model"), ("prompt_version", "wrong"), ("split", "test")):
                changed = {**metadata, field: value}
                (Path(tmp) / "run_metadata.json").write_text(json.dumps(changed))
                with self.assertRaises(SystemExit):
                    self.cli(*args)
            self.assertEqual(mocked.call_count, 3)

    def test_existing_synthetic_results_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp, patch("openai.OpenAI", side_effect=AssertionError("No API")):
            target = Path(tmp) / "judge_details.json"
            target.write_text('[{"domain":"banking_customer_onboarding"}]')
            before = target.read_bytes()
            with self.assertRaises(SystemExit):
                self.cli("--dataset", "tau2", "--domain", "retail", "--limit", "1", "--dry-run", "--output-dir", tmp)
            self.assertEqual(before, target.read_bytes())

    def test_synthetic_cannot_use_tau_output_folder(self):
        with self.assertRaises(SystemExit):
            self.cli("--dry-run", "--output-dir", str(DEFAULT_OUTPUT_DIR))

    def test_partial_judgments_survive_failure_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"OPENAI_API_KEY": "offline-test-placeholder"}), patch("openai.OpenAI"):
            args = ("--dataset", "tau2", "--domain", "airline", "--limit", "2", "--model", "gpt-6-luna", "--output-dir", tmp, "--resume")
            with patch.object(judge, "judge_task", side_effect=[self.judgment(), RuntimeError("Simulated API failure")]):
                with self.assertRaisesRegex(RuntimeError, "Failed evaluating"):
                    self.cli(*args)
            saved = json.loads((Path(tmp) / "judge_details.json").read_text())
            self.assertEqual(len(saved), 1)
            with patch.object(judge, "judge_task", return_value=self.judgment()) as mocked:
                self.cli(*args)
                self.assertEqual(mocked.call_count, 1)
            self.assertEqual(len(json.loads((Path(tmp) / "judge_details.json").read_text())), 2)


if __name__ == "__main__":
    unittest.main()
