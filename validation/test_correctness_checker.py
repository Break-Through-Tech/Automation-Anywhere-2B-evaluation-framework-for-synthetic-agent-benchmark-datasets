import unittest

from validation.correctness_checker import CHECKS, LLM_CHECKS, run_experiment, verdict


class ScoringTests(unittest.TestCase):
    def test_deterministic_partial_credit_and_inapplicable(self):
        checks = dict(zip(CHECKS, (1, 0, 1, None)))
        result = verdict(lambda task: {"checks": checks}, {})
        self.assertAlmostEqual(result["score"], 2 / 3)
        self.assertFalse(result["passed"])

    def test_invalid_scores_rejected(self):
        for values in ((1, 1, 1, .5), (None,) * 4, (1, 1, 1, float('nan'))):
            with self.assertRaises(ValueError):
                verdict(lambda task: {"checks": dict(zip(CHECKS, values))}, {})

    def test_llm_partial_credit_campaign(self):
        manifest = {
            "tasks": [{"id": "a", "expected_pass": True, "task": {"value": 1}},
                      {"id": "b", "task": {"value": 0}}],
            "mutations": [{"task_id": "a", "kind": "uncertain_outcome",
                           "expected_check": "expected_outcome",
                           "expected_checks": {"expected_outcome": .5},
                           "path": ["value"], "replacement": .5}],
        }
        def evaluator(task):
            checks = dict.fromkeys(LLM_CHECKS, 1)
            checks["expected_outcome"] = task["value"]
            return {"checks": checks}
        report = run_experiment(manifest, evaluator, rates=(0, 1), mode="llm")
        self.assertTrue(report["passed"])
        self.assertEqual(report["baseline_score"], .875)
        self.assertEqual(report["campaigns"][-1]["observed_score"], .8125)
        self.assertEqual(report["campaigns"][-1]["expected_score"], .8125)


if __name__ == "__main__":
    unittest.main()
