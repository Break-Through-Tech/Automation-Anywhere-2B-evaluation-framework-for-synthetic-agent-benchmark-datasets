from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from validation.correctness_checker import run_experiment
from evaluation.synthetic import (annotation_matches, corruption_manifest,
    evaluate, evaluate_dataset, load_dataset, python_inventory)

ROOT = Path(__file__).resolve().parents[1]


def clean_task():
    tool = {'name': 'lookup', 'args': [{'name': 'customer_id', 'type': 'string', 'required': True}]}
    case = {'test_case_id': 'a', 'title': 'Look up customer',
            'representative_input': {'customer_id': 'C1'},
            'expected_success_outcome': {'final_status': 'found'},
            'milestones': [{'step': 1, 'expected_state': {'found': True}}]}
    fixture = {'class_name': 'TestCaseA', 'attributes': {
        'test_case_id': 'a', 'workflow': 'W1', 'input_data': {'customer_id': 'C1'},
        'expected_tool_calls': [{'name': 'lookup', 'tool_inputs': {'customer_id': 'C1'}}],
        'milestones': deepcopy(case['milestones']),
        'expected_success_outcome': deepcopy(case['expected_success_outcome'])},
        'methods': {'lookup': {'args': {'customer_id': {'annotation': 'str', 'required': True}}}}}
    return {'case': case, 'python_fixture': fixture, 'tools': {'lookup': tool},
            'workflow': 'W1', 'agent': {'tools': {'system_tools': []}, 'workflows': [{'id': 'W1'}]}}


class DatasetTests(unittest.TestCase):
    def test_four_categories_and_dataset_average(self):
        task = clean_task()
        self.assertEqual(evaluate(task)['score'], 1)
        changed = deepcopy(task)
        changed['python_fixture']['attributes']['test_case_id'] = 'bad'
        self.assertEqual(evaluate(changed)['score'], .75)
        dataset = {'dataset': 'fixture', 'tasks': [{'id': 'a', 'task': task}, {'id': 'b', 'task': changed}],
                   'sources': {}, 'unmatched_python_classes': []}
        self.assertEqual(evaluate_dataset(dataset)['score'], .875)

    def test_corruption_campaigns_all_four_categories(self):
        dataset = {'tasks': [{'id': 'a', 'task': clean_task()}]}
        result = run_experiment(corruption_manifest(dataset), evaluate, rates=(0, 1))
        self.assertTrue(result['passed'])
        self.assertEqual({r['kind'] for r in result['campaigns']}, {
            'invalid_title_type', 'unknown_tool', 'inconsistent_case_id', 'inconsistent_expected_output'})
        self.assertIn('coverage_limits', result['audit'][0]['result'])

    def test_references_validate_partial_baseline(self):
        task = clean_task()
        task['case']['title'] = 123
        dataset = {'tasks': [{'id': 'a', 'task': task}]}
        result = run_experiment(corruption_manifest(dataset), evaluate, rates=(1,))
        row = next(r for r in result['campaigns'] if r['kind'] == 'inconsistent_case_id')
        self.assertEqual(row['eligible_tasks'], 1)
        self.assertTrue(row['passed'])

    def test_missing_output_evidence_is_inapplicable(self):
        task = clean_task()
        del task['python_fixture']['attributes']['milestones']
        del task['python_fixture']['attributes']['expected_success_outcome']
        result = evaluate(task)
        self.assertIsNone(result['checks']['output_consistency'])
        self.assertEqual(result['score'], 1)
        self.assertTrue(result['coverage_limits']['output_consistency'])

    def test_signature_types_and_enum(self):
        task = clean_task()
        task['tools']['lookup']['args'][0]['enum'] = ['C2']
        self.assertEqual(evaluate(task)['checks']['signatures'], 0)
        task['python_fixture']['attributes']['expected_tool_calls'][0]['tool_inputs']['customer_id'] = 1
        self.assertEqual(evaluate(task)['checks']['signatures'], 0)

    def test_typed_dict_and_nested_types(self):
        definitions = {'Customer': {'total': True, 'fields': {'age': 'int', 'tags': 'List[str]'}}}
        self.assertTrue(annotation_matches({'age': 3, 'tags': ['a']}, 'Customer', definitions))
        self.assertFalse(annotation_matches({'age': True, 'tags': ['a']}, 'Customer', definitions))
        self.assertFalse(annotation_matches({'age': 3, 'tags': [1]}, 'Customer', definitions))
        self.assertTrue(annotation_matches(None, 'Optional[str]', definitions))

    def test_python_reader_does_not_execute_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'test_cases.py'
            source.write_text("raise RuntimeError('must not execute')\nclass Base:\n    value = 1\nclass TestCaseA(Base):\n    test_case_id = 'a'\n")
            inventory = python_inventory(source)
            self.assertEqual(inventory[0]['attributes']['value'], 1)
            source.write_text("class TestCaseA:\n    input_data = {'id': 'C1'}\n    expected_tool_calls = [{'name': 'lookup', 'tool_inputs': {'id': input_data['id']}}]\n")
            inventory = python_inventory(source)
            self.assertEqual(inventory[0]['attributes']['expected_tool_calls'][0]['tool_inputs']['id'], 'C1')

    def test_all_repository_domains_load(self):
        paths = list((ROOT / 'data').glob('*/test_cases.json'))
        self.assertEqual(len(paths), 7)
        total = 0
        for path in paths:
            dataset = load_dataset(path.parent)
            report = evaluate_dataset(dataset)
            total += report['task_count']
            self.assertFalse(dataset['unmatched_python_classes'])
            self.assertTrue(all(t['task']['python_fixture'] for t in dataset['tasks']))
            self.assertTrue(0 <= report['score'] <= 1)
        self.assertEqual(total, 64)


if __name__ == '__main__':
    unittest.main()
