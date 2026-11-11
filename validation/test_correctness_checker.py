import unittest

from validation.correctness_checker import CHECKS, LLM_CHECKS, demo_manifest, reference_evaluator, run_experiment, verdict


class ScoringTests(unittest.TestCase):
    def test_nested_subsets_rounding_and_unexercised_campaigns(self):
        manifest = demo_manifest(3)
        report = run_experiment(manifest, reference_evaluator, rates=(0, .1, .5, 1))
        for kind in {row['kind'] for row in report['campaigns']}:
            selected = []
            for rate in (0, .1, .5, 1):
                selected.append({a['task_id'] for a in report['audit'] if a['kind'] == kind and a['rate'] == rate and a['corrupted']})
            self.assertEqual([len(s) for s in selected], [0, 0, 2, 3])
            self.assertTrue(all(a <= b for a, b in zip(selected, selected[1:])))
        manifest['campaign_names'] = ['unsupported']
        report = run_experiment(manifest, reference_evaluator)
        self.assertEqual(report['status'], 'inconclusive')
        self.assertIn('unsupported', report['unexercised_campaigns'])

    def test_crashes_propagate_and_false_positives_fail_validation(self):
        def crash(task):
            raise RuntimeError('evaluator crashed')
        with self.assertRaisesRegex(RuntimeError, 'evaluator crashed'):
            run_experiment(demo_manifest(), crash)
        def false_positive(task):
            result = reference_evaluator(task)
            result['checks']['schema'] = 0
            return result
        report = run_experiment(demo_manifest(), false_positive)
        self.assertEqual(report['status'], 'fail')
        self.assertEqual(report['baseline_false_positive_rate'], 1)

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
