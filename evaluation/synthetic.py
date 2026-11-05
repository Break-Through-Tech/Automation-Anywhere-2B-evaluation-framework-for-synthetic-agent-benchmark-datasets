"""Offline correctness checks for the repository's JSON/Python/YAML datasets.

Python sources are parsed, never imported or executed. This checks consistency
of recorded fixtures; it does not establish real-world tool executability.
"""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from correctness_op import deterministic_audit as audit
from validation.correctness_checker import CHECKS, score_checks


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def static_value(node, environment):
    """Resolve literals and earlier fixture references without executing Python."""
    if isinstance(node, ast.Name) and node.id in environment:
        return deepcopy(environment[node.id])
    if isinstance(node, ast.Subscript):
        return static_value(node.value, environment)[static_value(node.slice, environment)]
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [static_value(n, environment) for n in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.Dict):
        if any(k is None for k in node.keys):
            raise ValueError('Dictionary unpacking is not supported')
        return {static_value(k, environment): static_value(v, environment)
                for k, v in zip(node.keys, node.values)}
    return ast.literal_eval(node)


def literals(node, environment=None):
    result = deepcopy(environment or {})
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    try:
                        result[target.id] = static_value(item.value, result)
                    except (ValueError, TypeError, KeyError, IndexError):
                        pass
    return result


def python_inventory(path):
    """Extract fixture attributes and signatures, including local inheritance."""
    tree = ast.parse(Path(path).read_text())
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    typed_dicts = {}
    for name, node in classes.items():
        if any(isinstance(base, ast.Name) and base.id == 'TypedDict' for base in node.bases):
            total = not any(k.arg == 'total' and isinstance(k.value, ast.Constant) and k.value.value is False for k in node.keywords)
            typed_dicts[name] = {'total': total, 'fields': {
                n.target.id: ast.unparse(n.annotation) for n in node.body
                if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}}

    def collect(name, seen=()):
        if name in seen:
            raise ValueError(f"Cyclic class inheritance: {name}")
        attrs, methods = {}, {}
        node = classes[name]
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                a, m = collect(base.id, (*seen, name))
                attrs.update(a)
                methods.update(m)
        attrs.update(literals(node, attrs))
        for method in node.body:
            if isinstance(method, ast.FunctionDef) and not method.name.startswith('_'):
                defaults = [None] * (len(method.args.args) - len(method.args.defaults)) + list(method.args.defaults)
                parameters = list(zip(method.args.args, defaults))
                parameters += list(zip(method.args.kwonlyargs, method.args.kw_defaults))
                methods[method.name] = {
                    'args': {a.arg: {'annotation': ast.unparse(a.annotation) if a.annotation else None,
                                    'required': default is None}
                             for a, default in parameters if a.arg != 'self'},
                    'accepts_kwargs': method.args.kwarg is not None,
                    'source': ast.get_source_segment(Path(path).read_text(), method),
                }
        return attrs, methods

    return [{'class_name': name, 'attributes': collect(name)[0], 'methods': collect(name)[1], 'typed_dicts': typed_dicts}
            for name in classes if name.startswith('TestCase')]


def match_fixture(case, fixtures):
    """Use the PR's unique ID, then exact unique title matching convention."""
    references = []
    for fixture in fixtures:
        attrs = fixture['attributes']
        task_id = next((attrs[k] for k in audit.DEFAULT_CONFIG['python_id_fields'] if k in attrs), None)
        references.append({'cls': fixture['class_name'], 'fixture': fixture,
                           'test_id': task_id if isinstance(task_id, str) else None,
                           'title': attrs.get('title') if isinstance(attrs.get('title'), str) else None})
    reference, _ = audit.match_reference(case, references)
    if reference is None:
        return None, 'unmatched'
    method = 'id' if reference['test_id'] == case.get('test_case_id') else 'unique_title'
    return reference['fixture'], method


def load_dataset(directory):
    import yaml
    directory = Path(directory)
    paths = {name: directory / name for name in ('test_cases.json', 'test_cases.py', 'agent_definition.yaml')}
    document = json.loads(paths['test_cases.json'].read_text())
    definition = yaml.safe_load(paths['agent_definition.yaml'].read_text())
    agent = definition['agent']
    fixtures = python_inventory(paths['test_cases.py'])
    tools = {}
    for group in agent['tools'].values():
        for tool in group:
            if tool['name'] in tools:
                raise ValueError(f"Duplicate YAML tool: {tool['name']}")
            tools[tool['name']] = tool
    ids, tasks, used = set(), [], set()
    for workflow in document['workflows']:
        for case in workflow['test_cases']:
            task_id = case.get('test_case_id')
            if not isinstance(task_id, str) or task_id in ids:
                raise ValueError('JSON test_case_id must be a unique string')
            ids.add(task_id)
            fixture, match_method = match_fixture(case, fixtures)
            if fixture:
                used.add(fixture['class_name'])
            tasks.append({'id': task_id, 'task': {
                'case': case, 'workflow': workflow['workflow'].split(' - ')[0], 'agent': agent, 'tools': tools,
                'python_fixture': fixture, 'match_method': match_method if fixture else 'unmatched',
            }})
    if not tasks:
        raise ValueError('Dataset contains no tasks')
    return {'dataset': directory.name, 'tasks': tasks,
            'sources': {name: {'path': str(path.resolve()), 'sha256': fingerprint(path)} for name, path in paths.items()},
            'unmatched_python_classes': [f['class_name'] for f in fixtures if f['class_name'] not in used]}


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, (*path, index))
    else:
        yield path, value


def annotation_matches(value, annotation, definitions):
    """Use the PR's Python annotation rules; None means unsupported."""
    if not annotation:
        return None
    typed_dicts = {name: (definition['total'], {
        key: ast.parse(spec, mode='eval').body for key, spec in definition['fields'].items()})
        for name, definition in definitions.items()}
    return audit.annotation_matches(value, ast.parse(annotation, mode='eval').body, typed_dicts)


def evaluate(task):
    """Return binary category scores plus evidence and explicit coverage limits."""
    issues = {name: [] for name in CHECKS}
    coverage = {name: [] for name in CHECKS}
    applicable = dict.fromkeys(CHECKS, False)

    def fail(category, path, message):
        issues[category].append({'path': path, 'message': message})

    case, fixture, tools = task['case'], task.get('python_fixture'), task['tools']
    applicable['schema'] = True
    required = {'test_case_id': str, 'title': str, 'representative_input': dict,
                'expected_success_outcome': dict, 'milestones': list}
    for key, kind in required.items():
        if not isinstance(case.get(key), kind):
            fail('schema', f'case.{key}', f'Required {kind.__name__} value missing or invalid')
    outcome = case.get('expected_success_outcome')
    if isinstance(outcome, dict):
        for key, kind in (('final_status', str), ('key_outputs', dict)):
            if not isinstance(outcome.get(key), kind):
                fail('schema', f'case.expected_success_outcome.{key}',
                     f'Required {kind.__name__} value missing or invalid')
    milestones = case.get('milestones')
    if isinstance(milestones, list):
        steps = []
        for i, milestone in enumerate(milestones):
            if not isinstance(milestone, dict) or type(milestone.get('step')) is not int or not isinstance(milestone.get('expected_state'), dict):
                fail('schema', f'case.milestones.{i}', 'Milestone requires integer step and object expected_state')
            else:
                steps.append(milestone['step'])
        if steps != sorted(set(steps)):
            fail('schema', 'case.milestones', 'Steps must be unique and increasing')
    attrs = fixture['attributes'] if fixture else {}
    calls = attrs.get('expected_tool_calls')
    if fixture is None:
        fail('schema', 'python_fixture', 'No unambiguous Python fixture matches this case')
    elif not isinstance(calls, list):
        fail('schema', 'python_fixture.expected_tool_calls', 'Required list missing or not a literal')
    if isinstance(calls, list):
        applicable['signatures'] = True
        for i, call in enumerate(calls):
            path = f'python_fixture.attributes.expected_tool_calls.{i}'
            if not isinstance(call, dict) or not isinstance(call.get('name'), str) or not isinstance(call.get('tool_inputs'), dict):
                fail('schema', path, 'Call requires name and tool_inputs object')
                fail('signatures', path, 'Cannot validate malformed call')
                continue
            name, args = call['name'], call['tool_inputs']
            if name in audit.SYSTEM:
                params = {key: {'required': True, 'annotation': kind.__name__}
                          for key, kind in audit.SYSTEM[name].items()}
                accepts_kwargs = True
            else:
                if name not in tools:
                    fail('signatures', path, f'Unknown YAML tool: {name}')
                    continue
                method = fixture['methods'].get(name)
                if method is None:
                    fail('signatures', path, f'No Python tool method: {name}')
                    continue
                params = method['args']
                accepts_kwargs = method.get('accepts_kwargs', False)
            if ((not accepts_kwargs and args.keys() - params.keys())
                    or any(v['required'] and k not in args for k, v in params.items())):
                fail('signatures', path, f'Arguments disagree with Python method {name}')
            for key, value in args.items():
                if key in params and params[key]['annotation']:
                    match = annotation_matches(value, params[key]['annotation'], fixture.get('typed_dicts', {}))
                    if match is False:
                        fail('signatures', path, f'{key} disagrees with Python type {params[key]["annotation"]}')
                    elif match is None:
                        coverage['signatures'].append(f'Unsupported Python annotation: {name}.{key}')

    # Cross-file identities and workflow references are verifiable without a database.
    applicable['references'] = True
    if fixture:
        if match_fixture(case, [fixture])[0] is None:
            fail('references', 'python_fixture', 'Python counterpart matches neither task ID nor title')
        if attrs.get('input_data') != case.get('representative_input'):
            fail('references', 'python_fixture.attributes.input_data', 'Python value disagrees with JSON')
        if str(attrs.get('workflow', '')).split(' - ')[0] != task['workflow']:
            fail('references', 'python_fixture.attributes.workflow', 'Python workflow disagrees with JSON group')
    else:
        fail('references', 'python_fixture', 'Missing Python counterpart')
    workflow_ids = {w['id'] for w in task['agent'].get('workflows', [])}
    if task['workflow'] not in workflow_ids:
        fail('references', 'workflow', 'Workflow does not exist in YAML')
    # Input identifiers can be checked for consistency; generated IDs need outputs/state.
    input_ids = {}
    for path, value in leaves(case.get('representative_input', {})):
        if path and isinstance(path[-1], str) and path[-1].endswith('_id'):
            input_ids.setdefault(path[-1], []).append(value)
    if isinstance(calls, list):
        for i, call in enumerate(calls):
            if isinstance(call, dict):
                for path, value in leaves(call.get('tool_inputs', {})):
                    if path and path[-1] in input_ids and value not in input_ids[path[-1]]:
                        fail('references', f'expected_tool_calls.{i}.{path}', 'Identifier conflicts with task input')
    coverage['references'].append('No initial entity database or returned-entity provenance: existence of other IDs is unverified')
    if fixture:
        for source_key, fixture_key in (('expected_success_outcome', 'expected_success_outcome'), ('milestones', 'milestones')):
            if fixture_key in attrs and source_key in case:
                applicable['output_consistency'] = True
                if attrs[fixture_key] != case[source_key]:
                    fail('output_consistency', f'python_fixture.attributes.{fixture_key}', 'Expected values disagree between JSON and Python')
    coverage['output_consistency'].append('Cross-file expectations only; real tool execution and final-state outcome assertions are not available')
    checks = {key: (int(not issues[key]) if applicable[key] else None) for key in CHECKS}
    return {'checks': checks, 'score': score_checks(checks, CHECKS, 'deterministic'),
            'fully_evaluated': False,
            'outcome': {'status': 'not_evaluated', 'reason': 'Static consistency only; no real replay or independent final-state assertions'},
            'evidence': issues, 'coverage_limits': {k: sorted(set(v)) for k, v in coverage.items()}}


def evaluate_dataset(dataset, evaluator=evaluate, mode='deterministic'):
    from validation.correctness_checker import LLM_CHECKS, verdict
    categories = CHECKS if mode == 'deterministic' else LLM_CHECKS
    results = {}
    for entry in dataset['tasks']:
        raw = evaluator(deepcopy(entry['task']))
        checked = verdict(lambda _: raw, {}, categories, mode)
        results[entry['id']] = {**raw, **checked}
    return {'dataset': dataset['dataset'], 'mode': mode, 'task_count': len(results),
            'score': sum(r['score'] for r in results.values()) / len(results),
            'check_failures': {c: sum(r['checks'][c] is not None and r['checks'][c] < 1 for r in results.values()) for c in categories},
            'check_applicable_tasks': {c: sum(r['checks'][c] is not None for r in results.values()) for c in categories},
            'sources': dataset['sources'], 'unmatched_python_classes': dataset['unmatched_python_classes'],
            'results': results}


def corruption_manifest(dataset):
    """Known local mutations; expected target drops are independent of evaluator."""
    mutations = []
    for entry in dataset['tasks']:
        key, task = entry['id'], entry['task']
        fixture = task['python_fixture']
        cases = [('invalid_title_type', 'schema', ['case', 'title'], 123)]
        if fixture:
            unmatched = {**fixture['attributes'], 'title': '__corrupted_title__',
                         **{key: '__corrupted_id__' for key in audit.DEFAULT_CONFIG['python_id_fields']}}
            cases.append(('unmatched_python_reference', 'references', ['python_fixture', 'attributes'], unmatched))
            calls = fixture['attributes'].get('expected_tool_calls')
            if calls:
                cases.append(('unknown_tool', 'signatures', ['python_fixture', 'attributes', 'expected_tool_calls', 0, 'name'], '__unknown_tool__'))
            if 'milestones' in fixture['attributes']:
                cases.append(('inconsistent_expected_output', 'output_consistency', ['python_fixture', 'attributes', 'milestones'], []))
        for kind, check, path, replacement in cases:
            original = task
            for component in path:
                original = original[component]
            if original != replacement:
                mutation = {'task_id': key, 'kind': kind, 'expected_check': check,
                            'path': path, 'replacement': replacement}
                if (kind == 'invalid_title_type' and fixture
                        and match_fixture(task['case'], [fixture])[1] == 'unique_title'):
                    # Breaking the title also breaks a pairing that depends on it.
                    mutation['expected_checks'] = {'schema': 0, 'references': 0}
                mutations.append(mutation)
    return {'tasks': dataset['tasks'], 'mutations': mutations}


def main():
    from validation.correctness_checker import run_experiment
    from validation.reporting import evaluate_dataset as baseline_report
    from validation.reporting import terminal_summary, write_error, write_reports
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('output/synthetic-correctness'))
    parser.add_argument('--validate-corruptions', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--rates', type=float, nargs='+', default=[0, .1, .25, .5, 1])
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.dataset)
        dataset.update(subject='synthetic_static_consistency',
                       coverage_note='Static checks only; no real entity database or tool replay. Scores are not coverage-equivalent to tau2.')
        manifest = {**dataset, 'mutations': corruption_manifest(dataset)['mutations']} if args.validate_corruptions else dataset
        report = run_experiment(manifest, evaluate, args.rates, args.seed) if args.validate_corruptions else baseline_report(dataset, evaluate, args.seed)
        report['evaluator'] = 'evaluation.synthetic:evaluate'
        write_reports(report, manifest, args.output)
        print(terminal_summary(report, args.output))
        print('Coverage: static consistency only; no entity database or real tool replay.')
        return {'pass': 0, 'not_run': 0, 'fail': 1, 'inconclusive': 3}[report['status']]
    except Exception as error:
        try:
            path = write_error(error, args.output)
        except OSError:
            path = 'unavailable (output directory is not writable)'
        parser.exit(2, f'Evaluation error: {type(error).__name__}: {error}\nDiagnostics: {path}\n')


if __name__ == '__main__':
    raise SystemExit(main())


