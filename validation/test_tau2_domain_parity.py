"""Real-tool parity checks for airline and telecom corruption validation."""

from collections import Counter
from copy import deepcopy
import os
import unittest

from evaluation.tau2 import evaluate, load_dataset
from validation.correctness_checker import replace_at, run_experiment, verdict
from validation.tau2_corruptions import CAMPAIGNS, build_corruption_manifest, clean_controls


@unittest.skipUnless(os.environ.get("TAU2_BENCHMARK_ROOT"), "Set TAU2_BENCHMARK_ROOT for domain parity tests")
class DomainParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from loguru import logger
        logger.disable("tau2")
        cls.datasets = {domain: load_dataset(os.environ["TAU2_BENCHMARK_ROOT"], domain=domain)
                        for domain in ("airline", "telecom")}
        cls.controls = {domain: clean_controls(dataset) for domain, dataset in cls.datasets.items()}

    def test_all_seven_campaigns_have_twenty_clean_controls_per_domain(self):
        for domain, dataset in self.controls.items():
            with self.subTest(domain=domain):
                self.assertEqual(len({e["id"] for e in dataset["tasks"]}), 20)
                manifest = build_corruption_manifest(dataset)
                self.assertEqual(Counter(m["kind"] for m in manifest["mutations"]), dict.fromkeys(CAMPAIGNS, 20))
                self.assertFalse(manifest["excluded_mutations"])
                for entry in dataset["tasks"]:
                    result = verdict(evaluate, entry["task"])
                    self.assertTrue(result["passed"], entry["id"])
                    self.assertTrue(result["fully_evaluated"], entry["id"])
                    self.assertEqual(result["outcome"]["status"], "pass", entry["id"])

    def test_campaign_vectors_and_false_positives_for_both_domains(self):
        for domain, dataset in self.controls.items():
            with self.subTest(domain=domain):
                subset = {**dataset, "tasks": dataset["tasks"][:2]}
                report = run_experiment(build_corruption_manifest(subset), evaluate, rates=(0, 1))
                self.assertEqual(report["status"], "pass")
                self.assertEqual(report["baseline_false_positive_rate"], 0)
                self.assertFalse(report["unexercised_campaigns"])
                self.assertTrue(all(r["expected_check_vectors_matched"] == r["corrupted_tasks"] for r in report["campaigns"]))

    def test_telecom_no_argument_user_tools_get_real_signature_corruptions(self):
        dataset = self.datasets["telecom"]
        entry = next(e for e in dataset["tasks"]
                     if all(not a["arguments"] for a in e["task"]["definition"]["evaluation_criteria"]["actions"]))
        self.assertEqual(entry["task"]["definition"]["evaluation_criteria"]["actions"][0]["requestor"], "user")
        manifest = build_corruption_manifest({**dataset, "tasks": [entry]})
        for kind in ("wrong_type", "missing_argument"):
            mutation = next(m for m in manifest["mutations"] if m["kind"] == kind)
            task = deepcopy(entry["task"])
            replace_at(task, mutation["path"], mutation["replacement"])
            appended = task["definition"]["evaluation_criteria"]["actions"][-1]
            self.assertEqual(appended["name"], "get_customer_by_id")
            self.assertEqual(appended["requestor"], "assistant")
            self.assertEqual(evaluate(task)["checks"], mutation["expected_checks"])

    def test_airline_precondition_is_grounded_and_executable_failure(self):
        dataset = self.datasets["airline"]
        entry = next(e for e in dataset["tasks"] if e["task"]["definition"]["evaluation_criteria"]["actions"])
        mutation = next(m for m in build_corruption_manifest({**dataset, "tasks": [entry]})["mutations"]
                        if m["kind"] == "broken_precondition")
        task = deepcopy(entry["task"])
        replace_at(task, mutation["path"], mutation["replacement"])
        result = evaluate(task)
        self.assertEqual(result["checks"], mutation["expected_checks"])
        self.assertEqual(mutation["construction_rule"], "certificate_cannot_pay_for_reservation_update")
        self.assertIn("Certificate cannot be used", result["evidence"]["output_consistency"][0]["message"])

    def test_telecom_generic_entity_id_corruption_stays_in_references(self):
        dataset = deepcopy(self.controls["telecom"])
        dataset["tasks"] = dataset["tasks"][:1]
        first = dataset["tasks"][0]["task"]["definition"]["evaluation_criteria"]["actions"][0]
        first["name"] = "get_details_by_id"
        first["arguments"] = {"id": first["arguments"]["customer_id"]}
        mutation = next(m for m in build_corruption_manifest(dataset)["mutations"] if m["kind"] == "missing_entity")
        task = deepcopy(dataset["tasks"][0]["task"])
        replace_at(task, mutation["path"], mutation["replacement"])
        self.assertEqual(mutation["replacement"][:1], "C")
        self.assertEqual(evaluate(task)["checks"], mutation["expected_checks"])

    def test_telecom_precondition_and_user_actions_are_preserved(self):
        dataset = self.controls["telecom"]
        entry = dataset["tasks"][0]
        original = deepcopy(entry["task"])
        manifest = build_corruption_manifest({**dataset, "tasks": [entry]})
        self.assertEqual(entry["task"], original)
        mutation = next(m for m in manifest["mutations"] if m["kind"] == "broken_precondition")
        task = deepcopy(original)
        replace_at(task, mutation["path"], mutation["replacement"])
        result = evaluate(task)
        self.assertEqual(result["checks"], mutation["expected_checks"])
        self.assertIn("Refuel amount must be positive", result["evidence"]["output_consistency"][0]["message"])
        self.assertTrue(any(t["requestor"] == "user" and t["status"] == "executed" for t in result["trace"]))


if __name__ == "__main__":
    unittest.main()
