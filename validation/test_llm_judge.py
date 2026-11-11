import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from evaluation.llm_judge import Judge, parse_judgment
from validation.correctness_checker import LLM_CHECKS, verdict


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.task = {"request": 'Record "invoice A" for review.'}
        self.dimensions = {
            name: {"score": .5, "explanation": "Insufficient evidence", "evidence": []}
            for name in LLM_CHECKS
        }
        self.dimensions["task_consistency"] = {
            "score": 1, "explanation": "The request is internally consistent.",
            "evidence": [{"field": "request", "quote": '"invoice A"'}],
        }

    def test_full_rubric_includes_uncertainty_in_mean(self):
        result = verdict(lambda task: parse_judgment(json.dumps(self.dimensions), task),
                         self.task, LLM_CHECKS, "llm")
        self.assertEqual(result["score"], .625)

    def test_filters_unsubstantiated_quotes_and_rejects_boolean_scores(self):
        dimension = self.dimensions["task_consistency"]
        dimension["evidence"][0]["quote"] = "invoice B"
        result = parse_judgment(json.dumps(self.dimensions), self.task)
        self.assertEqual(result["dimensions"]["task_consistency"]["evidence"],
                         [{"field": "request", "quote": None}])
        dimension["score"] = True
        with self.assertRaisesRegex(ValueError, "Invalid judge response"):
            parse_judgment(json.dumps(self.dimensions), self.task)

    def test_repeated_campaign_input_reuses_one_judgment(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            model="returned-model", id="response-1", choices=[SimpleNamespace(
                finish_reason="stop", message=SimpleNamespace(
                    content=json.dumps(self.dimensions), refusal=None,
                ),
            )],
        )
        judge = Judge(client, "requested-model")
        first = judge(self.task)
        self.assertEqual(first, judge(dict(self.task)))
        self.assertEqual(first["judge"]["returned_model"], "returned-model")
        client.chat.completions.create.assert_called_once()
        schema = client.chat.completions.create.call_args.kwargs["response_format"]["json_schema"]["schema"]
        for name in LLM_CHECKS:
            evidence = schema["properties"][name]["properties"]["evidence"]["items"]
            self.assertEqual(evidence["properties"]["field"]["enum"], ["request"])
