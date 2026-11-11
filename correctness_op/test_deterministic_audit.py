"""Tests for deterministic_audit.py.

Run from the repo root:
  uv run python -m unittest discover -s correctness_op -v
"""
import ast
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deterministic_audit as da  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / 'data'
SCRIPT = Path(__file__).parent / 'deterministic_audit.py'

MOCK_PY = textwrap.dedent('''
    from typing import TypedDict, Optional

    class Profile(TypedDict, total=False):
        age: int
        student: bool

    class Tools:
        def get_order(self, order_id: str, verbose: bool = False):
            return {"order_id": order_id, "item_id": "I-9", "status": "open", "total": 50}

        def ship_item(self, item_id: str, profile: Profile):
            if item_id == "I-9":
                return {"shipment_id": "S-1", "carrier": "UPS"}
            return {"shipment_id": "S-0", "carrier": "none"}

    class TestCase1(Tools):
        test_case_id = "T1"
        title = "Ship an order"
        expected_tool_calls = [
            {"name": "get_order", "tool_inputs": {"order_id": "O-1"}},
            {"name": "ship_item", "tool_inputs": {"item_id": "I-9", "profile": {"age": 30}}},
            {"name": "SUCCESS", "tool_inputs": {"message": "done"}},
        ]
''')

MOCK_YAML = textwrap.dedent('''
    agent:
      tools:
        system_tools:
          - name: SUCCESS
        domain_tools:
          - name: get_order
          - name: ship_item
''')


def mock_task(**overrides):
    task = {
        'test_case_id': 'T1', 'title': 'Ship an order',
        'representative_input': {'order_id': 'O-1'},
        'expected_success_outcome': {'final_status': 'SUCCESS',
                                     'key_outputs': {'shipment_id': 'S-1', 'carrier': 'UPS'}},
        'milestones': [{'step': 1, 'description': 'fetch', 'expected_state': {'item_id': 'I-9'}},
                       {'step': 2, 'description': 'ship', 'expected_state': {'shipment_id': 'S-1'}}],
    }
    task.update(overrides)
    return task


def write_domain(root, task=None, py=MOCK_PY, yml=MOCK_YAML):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'test_cases.json').write_text(json.dumps({'workflows': [{'test_cases': [task or mock_task()]}]}))
    (root / 'test_cases.py').write_text(py)
    if yml is not None:
        (root / 'agent_definition.yaml').write_text(yml)
    return root


def statuses(checks, category):
    return [c['status'] for c in checks if c['category'] == category]


class DeclaredToolsTest(unittest.TestCase):
    @unittest.skipIf(da.yaml is None, 'PyYAML not installed')
    def test_grouped_tools_yield_tool_names_not_group_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            domain = write_domain(Path(tmp) / 'd')
            names, problem = da.load_declared_tools(domain)
        self.assertIsNone(problem)
        self.assertEqual(names, {'SUCCESS', 'get_order', 'ship_item'})

    @unittest.skipIf(da.yaml is None, 'PyYAML not installed')
    def test_tools_as_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            domain = write_domain(Path(tmp) / 'd', yml='tools:\n  get_order: {}\n  ship_item: {}\n')
            names, _ = da.load_declared_tools(domain)
        self.assertEqual(names, {'get_order', 'ship_item'})

    def test_missing_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            domain = write_domain(Path(tmp) / 'd', yml=None)
            names, problem = da.load_declared_tools(domain)
        self.assertIsNone(names)
        self.assertIn('no agent_definition.yaml', problem)


class AnnotationTest(unittest.TestCase):
    def match(self, value, ann, typed_dicts=None):
        return da.annotation_matches(value, ast.parse(ann, mode='eval').body, typed_dicts or {})

    def test_primitives(self):
        self.assertTrue(self.match(1, 'int'))
        self.assertFalse(self.match(True, 'int'))
        self.assertTrue(self.match(1, 'float'))
        self.assertFalse(self.match('1', 'float'))

    def test_containers(self):
        self.assertTrue(self.match(None, 'Optional[str]'))
        self.assertTrue(self.match(['a'], 'List[str]'))
        self.assertFalse(self.match(['a', 1], 'List[str]'))
        self.assertTrue(self.match({'a': 1}, 'Dict[str, int]'))
        self.assertTrue(self.match('x', "Literal['x', 'y']"))
        self.assertFalse(self.match('z', "Literal['x', 'y']"))

    def test_typed_dict(self):
        fields = {'age': ast.Name(id='int'), 'student': ast.Name(id='bool')}
        self.assertTrue(self.match({'age': 3}, 'P', {'P': (False, fields)}))
        self.assertFalse(self.match({'age': 3}, 'P', {'P': (True, fields)}))  # total=True needs all keys
        self.assertFalse(self.match({'student': None}, 'P', {'P': (False, fields)}))


class StaticReaderTest(unittest.TestCase):
    def method(self, src):
        return ast.parse(textwrap.dedent(src)).body[0]

    def test_branch_and_default(self):
        m = self.method('''
            def f(x, flag=True):
                if flag and x > 1:
                    return {"big": x}
                return {"small": x}
        ''')
        self.assertEqual(da.static_response(m, {'x': 5}), {'big': 5})
        self.assertEqual(da.static_response(m, {'x': 5, 'flag': False}), {'small': 5})

    def test_unsupported_code_is_unknown(self):
        m = self.method('def f(x):\n    import os\n    return os.getcwd()\n')
        self.assertIs(da.static_response(m, {'x': 1}), da.UNKNOWN)

    def test_boolean_operators_return_operand_values(self):
        for expression, value, expected in (
                ('x or "fallback"', 'C1', 'C1'),
                ('x or "fallback"', '', 'fallback'),
                ('x and "ready"', 'C1', 'ready'),
                ('x and "ready"', 0, 0),
                ('x and "ready"', [], []),
                ('x or [] or {"id": "C1"}', None, {'id': 'C1'})):
            with self.subTest(expression=expression, value=value):
                method = self.method(f'def f(x):\n    return {{"value": {expression}}}\n')
                actual = da.static_response(method, {'x': value})
                self.assertEqual(actual, {'value': expected})
                self.assertIs(type(actual['value']), type(expected))

    def test_boolean_operators_skip_unreachable_expressions(self):
        for expression, value in (('x or missing()', 'C1'), ('x and missing()', 0)):
            with self.subTest(expression=expression):
                method = self.method(f'def f(x):\n    return {expression}\n')
                self.assertEqual(da.static_response(method, {'x': value}), value)

    def test_huge_multiplication_is_refused(self):
        m = self.method('def f():\n    return "a" * 10**9\n')
        self.assertIs(da.static_response(m, {}), da.UNKNOWN)


class AuditDomainTest(unittest.TestCase):
    def audit(self, **task_overrides):
        with tempfile.TemporaryDirectory() as tmp:
            domain = write_domain(Path(tmp) / 'd', mock_task(**task_overrides))
            return da.audit_domain(domain, {}, da.DEFAULT_CONFIG)

    def test_clean_task_passes_everything(self):
        report = self.audit()
        task = report['tasks'][0]
        self.assertEqual(task['categories'], {c: 'PASS' for c in da.CATEGORIES})
        self.assertEqual(task['D_i'], 1.0)
        if da.yaml is not None:
            self.assertEqual(report['warnings'], [])

    def test_unreadable_json_has_complete_empty_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = da.audit_domain(Path(tmp), {}, da.DEFAULT_CONFIG)
        self.assertTrue(report['warnings'])
        self.assertEqual(report['tasks'], [])
        for key, value in da.summarize([]).items():
            self.assertEqual(report[key], value)

    def test_cli_reports_malformed_json_and_continues_other_domains(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / 'bad'
            bad.mkdir()
            (bad / 'test_cases.json').write_text('{bad json')
            write_domain(root / 'good')
            proc = subprocess.run([sys.executable, str(SCRIPT), '--data-dir', str(root)],
                                  capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('WARNING: test_cases.json unreadable:', proc.stdout)
        self.assertIn('=== good ===', proc.stdout)
        self.assertIn('=== ALL ===', proc.stdout)
        self.assertIn('Discovered: 1 | Audited: 1', proc.stdout)
        self.assertNotIn('Traceback', proc.stderr)

    def test_wrong_expected_output_fails(self):
        task = self.audit(expected_success_outcome={'final_status': 'SUCCESS',
                                                    'key_outputs': {'carrier': 'FedEx'}})['tasks'][0]
        self.assertEqual(task['categories']['output_consistency'], 'FAIL')

    def test_fabricated_id_fails_references(self):
        task = self.audit(representative_input={'order_id': 'O-OTHER'})['tasks'][0]
        self.assertEqual(task['categories']['references'], 'FAIL')

    def test_missing_reference_test(self):
        task = self.audit(test_case_id='NOPE', title='No such title')['tasks'][0]
        self.assertIsNone(task['reference_test'])
        self.assertEqual(task['categories']['signatures'], 'FAIL')

    def test_schema_step_order(self):
        bad = [{'step': 2, 'description': 'x', 'expected_state': {}}]
        task = self.audit(milestones=bad)['tasks'][0]
        self.assertEqual(task['categories']['schema'], 'FAIL')

    def test_test_class_mock_override_is_used(self):
        # The test class's own ship_item replaces the shared mock, so FedEx is correct here.
        override = ('    def ship_item(self, item_id: str, profile: Profile):\n'
                    '        return {"shipment_id": "S-1", "carrier": "FedEx"}\n\n'
                    '    expected_tool_calls = [')
        py = MOCK_PY.replace('    expected_tool_calls = [', override)
        outcome = {'final_status': 'SUCCESS', 'key_outputs': {'shipment_id': 'S-1', 'carrier': 'FedEx'}}
        with tempfile.TemporaryDirectory() as tmp:
            domain = write_domain(Path(tmp) / 'd', mock_task(expected_success_outcome=outcome), py=py)
            task = da.audit_domain(domain, {}, da.DEFAULT_CONFIG)['tasks'][0]
        self.assertEqual(task['categories']['output_consistency'], 'PASS')

    def test_duplicate_ids_across_domains(self):
        seen = {}
        with tempfile.TemporaryDirectory() as tmp:
            a = da.audit_domain(write_domain(Path(tmp) / 'a'), seen, da.DEFAULT_CONFIG)
            b = da.audit_domain(write_domain(Path(tmp) / 'b'), seen, da.DEFAULT_CONFIG)
        self.assertEqual(a['tasks'][0]['categories']['references'], 'PASS')
        self.assertEqual(b['tasks'][0]['categories']['references'], 'FAIL')


@unittest.skipUnless((DATA / 'banking_fraud_monitoring' / 'test_cases.json').exists(), 'repo data not present')
class RealDataTest(unittest.TestCase):
    """End-to-end run of the CLI over the repo's data/ folder."""

    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.run([sys.executable, str(SCRIPT), '--data-dir', str(DATA), '--details'],
                                  capture_output=True, text=True, timeout=300)
        seen = {}
        domains = sorted(p for p in DATA.iterdir() if p.is_dir() and (p / 'test_cases.json').exists())
        reports = [da.audit_domain(p, seen, da.DEFAULT_CONFIG) for p in domains]
        cls.details = {'overall': da.summarize([t for r in reports for t in r['tasks']]), 'domains': reports}
        cls.details['overall']['tasks_discovered'] = sum(r['tasks_discovered'] for r in reports)
        cls.details['overall']['tasks_skipped'] = sum(r['tasks_skipped'] for r in reports)

    def test_cli_prints_results_without_writing_files(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertIn('=== ALL ===', self.proc.stdout)
        self.assertIn('C_det=', self.proc.stdout)
        for domain in self.details['domains']:
            self.assertIn(f"=== {domain['domain']} ===", self.proc.stdout)
        self.assertFalse((REPO / 'audit_results').exists())

    def test_every_task_audited_and_scored(self):
        overall = self.details['overall']
        self.assertGreater(overall['tasks_audited'], 0)
        self.assertEqual(overall['tasks_audited'], overall['tasks_discovered'] - overall['tasks_skipped'])
        self.assertTrue(0 <= overall['C_det'] <= 1)
        for domain in self.details['domains']:
            for task in domain['tasks']:
                self.assertTrue(task['D_i'] is None or 0 <= task['D_i'] <= 1, task['task_id'])

    @unittest.skipIf(da.yaml is None, 'PyYAML not installed')
    def test_domain_tools_are_recognised_as_declared(self):
        # Regression: grouped YAML (tools.system_tools / tools.domain_tools) was read as two tools.
        for domain in self.details['domains']:
            joined = ' '.join(domain['warnings'])
            self.assertNotIn('domain_tools', joined, domain['domain'])
            for task in domain['tasks']:
                for c in task['checks']:
                    if c['message'].endswith('declared in agent definition'):
                        self.assertEqual(c['status'], 'PASS', (domain['domain'], task['task_id'], c['message']))


if __name__ == '__main__':
    unittest.main()
