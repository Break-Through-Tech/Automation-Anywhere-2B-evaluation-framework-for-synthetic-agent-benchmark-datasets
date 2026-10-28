"""Conservative static correctness audit for synthetic agent tasks.

Never imports test_cases.py, runs mock tools, or launches an agent/LLM.
Checks that cannot be established from source are marked UNVERIFIED.
"""
from __future__ import annotations
import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path

CATEGORIES = ('schema', 'signatures', 'references', 'output_consistency')
REQUIRED = {'test_case_id': str, 'title': str, 'representative_input': dict,
            'expected_success_outcome': dict, 'milestones': list}
SYSTEM = {'SUCCESS': {'message': str}, 'FAILED': {'message': str},
          'CANCELLED': {'message': str}, 'HUMAN_IN_THE_LOOP': {'ai_message': str}}
UNKNOWN = object()


def check(category, status, message, evidence=''):
    return dict(category=category, status=status, message=message, evidence=str(evidence))


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return UNKNOWN


def source_model(path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    tests, methods, typed_dicts = [], {}, {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        if any(isinstance(b, ast.Name) and b.id == 'TypedDict' for b in cls.bases):
            required = not any(k.arg == 'total' and literal(k.value) is False for k in cls.keywords)
            typed_dicts[cls.name] = (required, {
                s.target.id: s.annotation for s in cls.body if isinstance(s, ast.AnnAssign)
                and isinstance(s.target, ast.Name)})
        for stmt in cls.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == 'expected_tool_calls':
                        value = literal(stmt.value)
                        if isinstance(value, list):
                            tests.append({'title': next((literal(s.value) for s in cls.body
                                if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'title' for t in s.targets)), None),
                                          'calls': value, 'class': cls.name})
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods[stmt.name] = stmt
    return tests, methods, typed_dicts


def annotation_matches(value, ann, typed_dicts):
    """Return True, False, or None when a type cannot be checked statically."""
    if isinstance(ann, ast.Name):
        primitives = {'str': str, 'int': int, 'float': (int, float), 'bool': bool,
                      'dict': dict, 'list': list, 'Any': object}
        if ann.id in primitives:
            if ann.id == 'int': return type(value) is int
            if ann.id == 'float': return type(value) in (int, float)
            return isinstance(value, primitives[ann.id])
        if ann.id in typed_dicts:
            if not isinstance(value, dict): return False
            required, fields = typed_dicts[ann.id]
            if required and any(k not in value for k in fields): return False
            results = [annotation_matches(value[k], a, typed_dicts) for k, a in fields.items() if k in value]
            if False in results: return False
            return None if None in results else True
        return None
    if isinstance(ann, ast.Subscript):
        name = ann.value.id if isinstance(ann.value, ast.Name) else ''
        if name in ('Optional', 'Union'):
            if value is None: return True
            return annotation_matches(value, ann.slice, typed_dicts) if name == 'Optional' else None
        if name in ('List', 'list'):
            if not isinstance(value, list): return False
            results = [annotation_matches(v, ann.slice, typed_dicts) for v in value]
            return False if False in results else (None if None in results else True)
        if name in ('Dict', 'dict'):
            if not isinstance(value, dict): return False
            if isinstance(ann.slice, ast.Tuple) and len(ann.slice.elts) == 2:
                a, b = ann.slice.elts
                results = [annotation_matches(k, a, typed_dicts) for k in value]
                results += [annotation_matches(v, b, typed_dicts) for v in value.values()]
                return False if False in results else (None if None in results else True)
            return True
        if name == 'Literal':
            options = ann.slice.elts if isinstance(ann.slice, ast.Tuple) else [ann.slice]
            return value in [literal(x) for x in options]
    return None


def signature(method):
    args = method.args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    entries = [(a.arg, d is None, a.annotation) for a, d in zip(positional, defaults) if a.arg != 'self']
    entries += [(a.arg, d is None, a.annotation) for a, d in zip(args.kwonlyargs, args.kw_defaults)]
    return entries, bool(args.kwarg)


def schema_checks(task):
    out = []
    for key, kind in REQUIRED.items():
        valid = isinstance(task.get(key), kind) and (bool(task[key]) if kind is str else True)
        out.append(check('schema', 'PASS' if valid else 'FAIL', f'{key}: required {kind.__name__}'))
    outcome = task.get('expected_success_outcome')
    if isinstance(outcome, dict):
        for key, kind in [('final_status', str), ('key_outputs', dict)]:
            out.append(check('schema', 'PASS' if isinstance(outcome.get(key), kind) else 'FAIL',
                             f'expected_success_outcome.{key}: {kind.__name__}'))
    for i, m in enumerate(task.get('milestones', []) if isinstance(task.get('milestones'), list) else [], 1):
        valid = isinstance(m, dict) and isinstance(m.get('step'), int) and isinstance(m.get('description'), str) and isinstance(m.get('expected_state'), dict)
        out.append(check('schema', 'PASS' if valid else 'FAIL', f'milestone {i}: step, description, expected_state'))
        if valid:
            out.append(check('schema', 'PASS' if m['step'] == i else 'FAIL', f'milestone {i}: step order'))
    return out


def signature_checks(calls, methods, typed_dicts):
    out = []
    for i, call in enumerate(calls, 1):
        if not isinstance(call, dict) or not isinstance(call.get('name'), str) or not isinstance(call.get('tool_inputs'), dict):
            out.append(check('signatures', 'FAIL', f'call {i}: malformed call')); continue
        name, inputs = call['name'], call['tool_inputs']
        method = methods.get(name)
        if method:
            entries, kwargs = signature(method)
        elif name in SYSTEM:
            entries = [(k, True, ast.Name(id=v.__name__, ctx=ast.Load())) for k, v in SYSTEM[name].items()]
            # System tool optional arguments are handled by the base runtime.
            kwargs = True
        else:
            out.append(check('signatures', 'FAIL', f'call {i}: unknown tool {name}')); continue
        out.append(check('signatures', 'PASS', f'call {i}: tool {name} exists'))
        required = {k for k, req, _ in entries if req}
        allowed = {k for k, _, _ in entries}
        missing = required - inputs.keys()
        extra = set(inputs) - allowed if not kwargs else set()
        out.append(check('signatures', 'FAIL' if missing or extra else 'PASS',
                         f'call {i}: {name} argument names', f'missing={sorted(missing)} extra={sorted(extra)}'))
        for k, _, ann in entries:
            if k not in inputs or ann is None: continue
            valid = annotation_matches(inputs[k], ann, typed_dicts)
            out.append(check('signatures', 'UNVERIFIED' if valid is None else ('PASS' if valid else 'FAIL'),
                             f'call {i}: {name}.{k} argument type', f'value type={type(inputs[k]).__name__}'))
    return out


def leaves(value, prefix=''):
    if isinstance(value, dict):
        for key, v in value.items(): yield from leaves(v, f'{prefix}.{key}' if prefix else key)
    elif not isinstance(value, list):
        yield prefix, value


def reference_checks(task, calls, seen_ids):
    out = []
    task_id = task.get('test_case_id')
    out.append(check('references', 'FAIL' if task_id in seen_ids else 'PASS', 'unique task ID'))
    if isinstance(task_id, str): seen_ids.add(task_id)
    source = task.get('representative_input', {})
    if not isinstance(source, dict): return out
    for i, call in enumerate(calls, 1):
        inputs = call.get('tool_inputs', {}) if isinstance(call, dict) else {}
        if not isinstance(inputs, dict): continue
        for k in set(source) & set(inputs):
            if k.endswith('_id') or k in ('document_files', 'account_type', 'policy_number', 'application_id'):
                same = source[k] == inputs[k]
                out.append(check('references', 'PASS' if same else 'FAIL', f'call {i}: input {k} reference',
                                 f'input={source[k]!r}; call={inputs[k]!r}'))
    # Repeated IDs can legitimately refer to different objects, so don't assume equality.
    if len(out) == 1: out.append(check('references', 'UNVERIFIED', 'no unambiguous input references'))
    return out


def cross_call_reference_checks(task, calls, methods):
    """Compare downstream IDs only when a unique earlier tool produced that ID."""
    out = []
    initial = task.get('representative_input', {})
    if not isinstance(initial, dict): initial = {}
    previous = []
    for index, call in enumerate(calls, 1):
        if not isinstance(call, dict): continue
        inputs = call.get('tool_inputs', {})
        if not isinstance(inputs, dict): continue
        for key, value in inputs.items():
            if not key.endswith('_id') or key in initial: continue
            producers = [(n, tool, response[key]) for n, tool, response in previous
                         if isinstance(response, dict) and key in response]
            if len(producers) == 1:
                n, tool, produced = producers[0]
                out.append(check('references', 'PASS' if value == produced else 'FAIL',
                                 f'call {index}: {key} from earlier {tool} (call {n})',
                                 f'produced={produced!r}; supplied={value!r}'))
            elif len(producers) > 1:
                out.append(check('references', 'UNVERIFIED', f'call {index}: {key} has multiple producers'))
        method = methods.get(call.get('name'))
        if method:
            previous.append((index, call['name'], static_response(method, inputs)))
    return out


class Unsupported(Exception): pass


def eval_expr(node, env):
    """Interpret a small safe subset of Python expressions; never call user code."""
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, ast.Name):
        if node.id not in env: raise Unsupported()
        return env[node.id]
    if isinstance(node, ast.Dict): return {eval_expr(k, env): eval_expr(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple)): return [eval_expr(x, env) for x in node.elts]
    if isinstance(node, ast.Subscript): return eval_expr(node.value, env)[eval_expr(node.slice, env)]
    if isinstance(node, ast.Attribute): raise Unsupported()
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        obj = eval_expr(node.func.value, env)
        if node.func.attr == 'get' and isinstance(obj, dict) and len(node.args) in (1, 2):
            return obj.get(*(eval_expr(a, env) for a in node.args))
        if node.func.attr == 'lower' and isinstance(obj, str) and not node.args: return obj.lower()
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        a, b = eval_expr(node.left, env), eval_expr(node.comparators[0], env)
        op = node.ops[0]
        if isinstance(op, ast.Eq): return a == b
        if isinstance(op, ast.NotEq): return a != b
        if isinstance(op, ast.Gt): return a > b
        if isinstance(op, ast.Lt): return a < b
        if isinstance(op, ast.GtE): return a >= b
        if isinstance(op, ast.LtE): return a <= b
        if isinstance(op, ast.In): return a in b
        if isinstance(op, ast.NotIn): return a not in b
    if isinstance(node, ast.BoolOp):
        vals = [bool(eval_expr(x, env)) for x in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not): return not eval_expr(node.operand, env)
    if isinstance(node, ast.BinOp):
        a, b = eval_expr(node.left, env), eval_expr(node.right, env)
        if isinstance(node.op, ast.Add): return a + b
        if isinstance(node.op, ast.Sub): return a - b
        if isinstance(node.op, ast.Mult): return a * b
    raise Unsupported()


def interpret(statements, env):
    """Static evaluation of straightforward assignments, branches and returns."""
    for stmt in statements:
        if isinstance(stmt, ast.Return): return eval_expr(stmt.value, env)
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            env[stmt.targets[0].id] = eval_expr(stmt.value, env)
        elif isinstance(stmt, ast.If):
            branch = stmt.body if eval_expr(stmt.test, env) else stmt.orelse
            result = interpret(branch, env)
            if result is not UNKNOWN: return result
        elif isinstance(stmt, ast.Pass):
            continue
        elif isinstance(stmt, ast.Expr):
            # Ignore only docstrings and print statements; other calls may mutate state.
            expr = stmt.value
            if isinstance(expr, ast.Constant) and isinstance(expr.value, str): continue
            if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == 'print': continue
            raise Unsupported()
        else:
            raise Unsupported()
    return UNKNOWN


def static_response(method, inputs):
    try:
        return interpret(method.body, dict(inputs))
    except (Unsupported, KeyError, TypeError, ValueError, ZeroDivisionError, IndexError, AttributeError):
        return UNKNOWN


def output_checks(task, calls, methods):
    out = []
    milestones = task.get('milestones', [])
    expected = []
    for i, milestone in enumerate(milestones if isinstance(milestones, list) else [], 1):
        if isinstance(milestone, dict) and isinstance(milestone.get('expected_state'), dict):
            for key, value in leaves(milestone['expected_state']): expected.append((f'milestone {i}', key, value))
    outcome = task.get('expected_success_outcome', {})
    if isinstance(outcome, dict):
        for key, value in leaves(outcome.get('key_outputs', {})): expected.append(('final output', key, value))
    responses = []
    for i, call in enumerate(calls, 1):
        method = methods.get(call.get('name')) if isinstance(call, dict) else None
        inputs = call.get('tool_inputs') if isinstance(call, dict) else None
        if method is None or not isinstance(inputs, dict): continue
        response = static_response(method, inputs)
        responses.append((i, call['name'], response))
    if not responses:
        return [check('output_consistency', 'UNVERIFIED', 'no analyzable mock tool responses')]
    # Match exact field names only when a single producer is identifiable.
    generic = {'status', 'name', 'id', 'type', 'date', 'amount', 'time', 'method', 'timestamp', 'decision_notes'}
    for location, path, value in expected:
        leaf = path.rsplit('.', 1)[-1]
        # Generic fields require a clearly identified producing tool.
        if leaf in generic:
            out.append(check('output_consistency', 'UNVERIFIED', f'{location}.{path}: generic field, producer ambiguous'))
            continue
        candidates = [(i, name, response[leaf]) for i, name, response in responses
                      if isinstance(response, dict) and leaf in response]
        if len(candidates) == 1:
            i, name, actual = candidates[0]
            out.append(check('output_consistency', 'PASS' if actual == value else 'FAIL',
                             f'{location}.{path} vs {name} (call {i})',
                             f'expected={value!r}; static response={actual!r}'))
        elif len(candidates) > 1:
            out.append(check('output_consistency', 'UNVERIFIED', f'{location}.{path}: multiple potential producers'))
        else:
            out.append(check('output_consistency', 'UNVERIFIED', f'{location}.{path}: mock output not statically resolved'))
    if not out: out.append(check('output_consistency', 'UNVERIFIED', 'no comparable expected outputs'))
    return out


def summary(checks):
    counts = Counter(c['status'] for c in checks)
    p, f, u = (counts[k] for k in ('PASS', 'FAIL', 'UNVERIFIED'))
    return dict(score=round(p/(p+f), 4) if p+f else None,
                verification_coverage=round((p+f)/(p+f+u), 4) if p+f+u else None,
                passed=p, failed=f, unverified=u)


def audit_domain(domain):
    data = json.loads((domain/'test_cases.json').read_text(encoding='utf-8'))
    tests, methods, typed_dicts = source_model(domain/'test_cases.py')
    titles = {}
    for test in tests: titles.setdefault(test['title'], []).append(test)
    seen, records = set(), []
    for workflow in data.get('workflows', []):
        for task in workflow.get('test_cases', []):
            matches = titles.get(task.get('title'), [])
            calls = matches[0]['calls'] if len(matches) == 1 else []
            checks = schema_checks(task)
            checks.append(check('references', 'PASS' if len(matches) == 1 else 'FAIL',
                                'unique JSON-to-Python task title match'))
            checks += reference_checks(task, calls, seen)
            checks += cross_call_reference_checks(task, calls, methods)
            checks += signature_checks(calls, methods, typed_dicts) if len(matches) == 1 else [
                check('signatures', 'UNVERIFIED', 'reference calls unavailable')]
            checks += output_checks(task, calls, methods)
            records.append(dict(domain=domain.name, task_id=task.get('test_case_id'),
                                title=task.get('title'), checks=checks, **summary(checks),
                                categories={c: summary([x for x in checks if x['category'] == c]) for c in CATEGORIES}))
    return dict(domain=domain.name, tasks=records, task_count=len(records), **summary(
        [c for r in records for c in r['checks']]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=Path('audit_results'))
    args = parser.parse_args()
    domains = sorted(p for p in args.data_dir.iterdir() if p.is_dir() and
                     (p/'test_cases.json').exists() and (p/'test_cases.py').exists())
    if not domains: parser.error('No valid dataset domains found')
    reports = [audit_domain(p) for p in domains]
    tasks = [t for d in reports for t in d['tasks']]
    aggregate = summary([c for t in tasks for c in t['checks']])
    # The overall correctness score is the mean of task scores, not the pooled check rate.
    scored = [t['score'] for t in tasks if t['score'] is not None]
    aggregate['score'] = round(sum(scored)/len(scored), 4) if scored else None
    aggregate['task_count'] = len(tasks)
    aggregate['domains'] = len(reports)
    for report in reports:
        scores = [t['score'] for t in report['tasks'] if t['score'] is not None]
        report['score'] = round(sum(scores)/len(scores), 4) if scores else None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'audit_details.json').write_text(json.dumps({'domains': reports, 'overall': aggregate}, indent=2), encoding='utf-8')
    for filename, rows, columns in [
        ('task_scores.csv', tasks, ['domain','task_id','score','verification_coverage','passed','failed','unverified']),
        ('domain_scores.csv', reports, ['domain','task_count','score','verification_coverage','passed','failed','unverified'])]:
        with (args.output_dir/filename).open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
    print(f"Audited {len(tasks)} tasks in {len(reports)} domains")
    print(f"Correctness: {aggregate['score']}; verification coverage: {aggregate['verification_coverage']}")
    print(f"PASS={aggregate['passed']} FAIL={aggregate['failed']} UNVERIFIED={aggregate['unverified']}")
    print(f"Results: {args.output_dir}")


if __name__ == '__main__': main()

