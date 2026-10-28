"""Deterministic correctness audit for synthetic agent tasks (v2).

Static only: never imports test_cases.py, runs mock tools, or calls an LLM.
Anything that cannot be established from source is marked UNVERIFIED.
Requires Python 3.9+ and PyYAML (for agent_definition.yaml).

Scoring
  Each task gets one status per category (Schema, Signatures, References,
  Output_Consistency):
    FAIL        if any check in the category fails
    PASS        if at least one check passes and none fail
    UNVERIFIED  otherwise (the category is left out of the score)
  D_i     = passed categories / scorable categories        (task score)
  V_i     = scorable categories / 4                        (task coverage)
  C_det   = mean of D_i over scorable tasks                (dataset score)
  Cov_det = scorable tasks / audited tasks                 (dataset coverage)

Usage
  python deterministic_audit.py --data-dir DATA [--output-dir OUT] [--config CFG]
  DATA is either one domain folder or a folder of domain folders. Each domain
  needs test_cases.json, test_cases.py and agent_definition.yaml. An optional
  audit_config.json in a domain folder overrides --config for that domain.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    sys.exit('deterministic_audit.py requires Python 3.9 or newer')

import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:  # Declaration checks become UNVERIFIED without PyYAML.
    yaml = None

CATEGORIES = ('schema', 'signatures', 'references', 'output_consistency')
REQUIRED = {'test_case_id': str, 'title': str, 'representative_input': dict,
            'expected_success_outcome': dict, 'milestones': list}
SYSTEM = {'SUCCESS': {'message': str}, 'FAILED': {'message': str},
          'CANCELLED': {'message': str}, 'HUMAN_IN_THE_LOOP': {'ai_message': str}}
YAML_NAMES = ('agent_definition.yaml', 'agent_definition.yml', 'agent_defintion.yaml')
TOOL_LIST_KEYS = ('tools', 'available_tools', 'tool_definitions')
NOT_TOOLS = {'setUp', 'tearDown', 'setUpClass', 'tearDownClass'}
DEFAULT_CONFIG = {
    # Keys checked for provenance in addition to any key ending in "_id".
    'reference_keys': ['document_files', 'policy_number'],
    # Top-level fields too common to attribute to one tool by name alone.
    'generic_fields': ['status', 'name', 'id', 'type', 'date', 'amount', 'time',
                       'method', 'timestamp', 'decision_notes'],
    # Class attributes in test_cases.py that may hold the task ID.
    'python_id_fields': ['test_case_id', 'task_id'],
}
MAX_SEQUENCE = 10_000  # Cap on strings/lists built by multiplication in the code reader.
UNKNOWN = object()
MISSING = object()


def check(category, status, message, evidence=''):
    return dict(category=category, status=status, message=message, evidence=str(evidence))


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, RecursionError, MemoryError):
        return UNKNOWN


def load_config(domain, base):
    config = {k: list(v) for k, v in base.items()}
    path = domain / 'audit_config.json'
    if path.exists():
        config.update(json.loads(path.read_text(encoding='utf-8')))
    return config


# ---------------------------------------------------------------- source reading

def source_model(path, id_fields):
    """Split test_cases.py into reference tests, mock tool methods and TypedDicts."""
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    tests, tool_defs, typed_dicts = [], {}, {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        if any(isinstance(b, ast.Name) and b.id == 'TypedDict' for b in cls.bases):
            required = not any(k.arg == 'total' and literal(k.value) is False for k in cls.keywords)
            typed_dicts[cls.name] = (required, {
                s.target.id: s.annotation for s in cls.body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)})
            continue
        assigns = {}
        for stmt in cls.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        assigns[target.id] = stmt.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value:
                assigns[stmt.target.id] = stmt.value
        if 'expected_tool_calls' in assigns:
            # A reference test class. Its methods are test plumbing, never tools.
            calls = literal(assigns['expected_tool_calls'])
            title = literal(assigns['title']) if 'title' in assigns else None
            test_id = next((literal(assigns[f]) for f in id_fields if f in assigns), None)
            tests.append(dict(cls=cls.name,
                              title=title if isinstance(title, str) else None,
                              test_id=test_id if isinstance(test_id, str) else None,
                              calls=calls if isinstance(calls, list) else None))
            continue
        for stmt in cls.body:
            if (isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not stmt.name.startswith(('_', 'test')) and stmt.name not in NOT_TOOLS):
                tool_defs.setdefault(stmt.name, []).append((cls.name, stmt))
    return tests, tool_defs, typed_dicts


def load_declared_tools(domain):
    """Return (set of tool names declared in the agent definition, problem)."""
    path = next((domain / n for n in YAML_NAMES if (domain / n).exists()), None)
    if path is None:
        return None, 'no agent_definition.yaml found'
    if yaml is None:
        return None, 'PyYAML is not installed'
    try:
        doc = yaml.safe_load(path.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001 - report any YAML problem, keep auditing
        return None, f'{path.name} could not be parsed: {exc}'
    names, found = set(), False

    def walk(node):
        nonlocal found
        if isinstance(node, dict):
            for key, value in node.items():
                if key in TOOL_LIST_KEYS and isinstance(value, dict):
                    found = True
                    names.update(k for k in value if isinstance(k, str))
                elif key in TOOL_LIST_KEYS and isinstance(value, list):
                    found = True
                    for item in value:
                        if isinstance(item, str):
                            names.add(item)
                        elif isinstance(item, dict):
                            name = item.get('name') or item.get('tool_name') or (
                                item.get('function') or {}).get('name')
                            if isinstance(name, str):
                                names.add(name)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc)
    if not found:
        return None, f'no tools list found in {path.name}'
    return names, None


def resolve_tool(name, tool_defs):
    """Return (method, problem). Same-named methods with identical signatures are fine."""
    defs = tool_defs.get(name, [])
    if not defs:
        return None, 'missing'
    if len({ast.dump(d.args) for _, d in defs}) > 1:
        return None, 'ambiguous: ' + ', '.join(c for c, _ in defs)
    return defs[0][1], None


# ---------------------------------------------------------------- type checking

def annotation_matches(value, ann, typed_dicts):
    """Return True, False, or None when a type cannot be checked statically."""
    if isinstance(ann, ast.Name):
        primitives = {'str': str, 'int': int, 'float': (int, float), 'bool': bool,
                      'dict': dict, 'list': list, 'Any': object}
        if ann.id in primitives:
            if ann.id == 'int':
                return type(value) is int
            if ann.id == 'float':
                return type(value) in (int, float)
            return isinstance(value, primitives[ann.id])
        if ann.id in typed_dicts:
            if not isinstance(value, dict):
                return False
            required, fields = typed_dicts[ann.id]
            if required and any(k not in value for k in fields):
                return False
            results = [annotation_matches(value[k], a, typed_dicts) for k, a in fields.items() if k in value]
            if False in results:
                return False
            return None if None in results else True
        return None
    if isinstance(ann, ast.Subscript):
        name = ann.value.id if isinstance(ann.value, ast.Name) else ''
        if name in ('Optional', 'Union'):
            if value is None:
                return True
            return annotation_matches(value, ann.slice, typed_dicts) if name == 'Optional' else None
        if name in ('List', 'list'):
            if not isinstance(value, list):
                return False
            results = [annotation_matches(v, ann.slice, typed_dicts) for v in value]
            return False if False in results else (None if None in results else True)
        if name in ('Dict', 'dict'):
            if not isinstance(value, dict):
                return False
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


# ---------------------------------------------------------------- static code reader

class Unsupported(Exception):
    pass


def eval_expr(node, env):
    """Interpret a small safe subset of Python expressions; never call user code."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise Unsupported()
        return env[node.id]
    if isinstance(node, ast.Dict):
        if any(k is None for k in node.keys):  # {**other} unpacking
            raise Unsupported()
        return {eval_expr(k, env): eval_expr(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple)):
        return [eval_expr(x, env) for x in node.elts]
    if isinstance(node, ast.Subscript):
        return eval_expr(node.value, env)[eval_expr(node.slice, env)]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        obj = eval_expr(node.func.value, env)
        if node.func.attr == 'get' and isinstance(obj, dict) and len(node.args) in (1, 2):
            return obj.get(*(eval_expr(a, env) for a in node.args))
        if node.func.attr == 'lower' and isinstance(obj, str) and not node.args:
            return obj.lower()
        raise Unsupported()
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        a, b = eval_expr(node.left, env), eval_expr(node.comparators[0], env)
        op = node.ops[0]
        ops = {ast.Eq: lambda: a == b, ast.NotEq: lambda: a != b, ast.Gt: lambda: a > b,
               ast.Lt: lambda: a < b, ast.GtE: lambda: a >= b, ast.LtE: lambda: a <= b,
               ast.In: lambda: a in b, ast.NotIn: lambda: a not in b}
        if type(op) in ops:
            return ops[type(op)]()
    if isinstance(node, ast.BoolOp):
        values = [bool(eval_expr(x, env)) for x in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not eval_expr(node.operand, env)
    if isinstance(node, ast.BinOp):
        a, b = eval_expr(node.left, env), eval_expr(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            for seq, n in ((a, b), (b, a)):
                if isinstance(seq, (str, list)) and isinstance(n, int) and len(seq) * max(n, 0) > MAX_SEQUENCE:
                    raise Unsupported()
            return a * b
    raise Unsupported()


def interpret(statements, env):
    """Static evaluation of straightforward assignments, branches and returns."""
    for stmt in statements:
        if isinstance(stmt, ast.Return):
            return eval_expr(stmt.value, env) if stmt.value is not None else None
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            env[stmt.targets[0].id] = eval_expr(stmt.value, env)
        elif isinstance(stmt, ast.If):
            result = interpret(stmt.body if eval_expr(stmt.test, env) else stmt.orelse, env)
            if result is not UNKNOWN:
                return result
        elif isinstance(stmt, ast.Pass):
            continue
        elif isinstance(stmt, ast.Expr):
            # Ignore only docstrings and print(); other calls may mutate state.
            expr = stmt.value
            if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
                continue
            if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == 'print':
                continue
            raise Unsupported()
        else:
            raise Unsupported()
    return UNKNOWN


def static_response(method, inputs):
    """Predict a mock tool's return value, filling in literal default arguments."""
    env = dict(inputs)
    args = method.args
    positional = args.posonlyargs + args.args
    pairs = list(zip(positional[len(positional) - len(args.defaults):], args.defaults))
    pairs += [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None]
    for arg, default in pairs:
        if arg.arg not in env:
            value = literal(default)
            if value is not UNKNOWN:
                env[arg.arg] = value
    try:
        return interpret(method.body, env)
    except (Unsupported, KeyError, TypeError, ValueError, ZeroDivisionError, IndexError,
            AttributeError, RecursionError, MemoryError, OverflowError):
        return UNKNOWN


def predict_responses(calls, tool_defs):
    """One entry per call: predicted response, UNKNOWN, or None for system tools."""
    responses = []
    for call in calls:
        if not isinstance(call, dict) or call.get('name') in SYSTEM:
            responses.append(None)
            continue
        method, _ = resolve_tool(call.get('name'), tool_defs)
        inputs = call.get('tool_inputs')
        responses.append(static_response(method, inputs) if method and isinstance(inputs, dict) else UNKNOWN)
    return responses


# ---------------------------------------------------------------- helpers

def leaves(value, prefix=''):
    """Yield (dotted path, value). Lists are treated as whole values."""
    if isinstance(value, dict):
        for key, v in value.items():
            yield from leaves(v, f'{prefix}.{key}' if prefix else str(key))
    elif prefix:
        yield prefix, value


def scalar_values(value):
    """All str/int/float/bool values nested anywhere inside value."""
    if isinstance(value, dict):
        for v in value.values():
            yield from scalar_values(v)
    elif isinstance(value, list):
        for v in value:
            yield from scalar_values(v)
    elif isinstance(value, (str, int, float, bool)):
        yield value


def get_path(obj, path):
    for part in path.split('.'):
        if not isinstance(obj, dict) or part not in obj:
            return MISSING
        obj = obj[part]
    return obj


# ---------------------------------------------------------------- checks

def schema_checks(task):
    out = []
    for key, kind in REQUIRED.items():
        valid = isinstance(task.get(key), kind) and (bool(task[key]) if kind is str else True)
        out.append(check('schema', 'PASS' if valid else 'FAIL', f'{key}: required {kind.__name__}'))
    outcome = task.get('expected_success_outcome')
    if isinstance(outcome, dict):
        for key, kind in (('final_status', str), ('key_outputs', dict)):
            out.append(check('schema', 'PASS' if isinstance(outcome.get(key), kind) else 'FAIL',
                             f'expected_success_outcome.{key}: {kind.__name__}'))
    milestones = task.get('milestones')
    for i, m in enumerate(milestones if isinstance(milestones, list) else [], 1):
        valid = (isinstance(m, dict) and type(m.get('step')) is int
                 and isinstance(m.get('description'), str) and isinstance(m.get('expected_state'), dict))
        out.append(check('schema', 'PASS' if valid else 'FAIL', f'milestone {i}: step, description, expected_state'))
        if valid:
            out.append(check('schema', 'PASS' if m['step'] == i else 'FAIL', f'milestone {i}: step order',
                             f'step={m["step"]}'))
    return out


def signature_checks(calls, tool_defs, typed_dicts, declared, declared_problem):
    out = []
    for i, call in enumerate(calls, 1):
        if not isinstance(call, dict) or not isinstance(call.get('name'), str) \
                or not isinstance(call.get('tool_inputs'), dict):
            out.append(check('signatures', 'FAIL', f'call {i}: malformed call'))
            continue
        name, inputs = call['name'], call['tool_inputs']
        if name in SYSTEM:
            out.append(check('signatures', 'PASS', f'call {i}: {name} is a built-in system tool'))
            entries = [(k, True, ast.Name(id=v.__name__, ctx=ast.Load())) for k, v in SYSTEM[name].items()]
            kwargs = True  # Optional system-tool arguments are handled by the base runtime.
        else:
            if declared is None:
                out.append(check('signatures', 'UNVERIFIED', f'call {i}: {name} declaration not checked',
                                 declared_problem))
            else:
                out.append(check('signatures', 'PASS' if name in declared else 'FAIL',
                                 f'call {i}: {name} declared in agent definition'))
            method, problem = resolve_tool(name, tool_defs)
            if problem == 'missing':
                out.append(check('signatures', 'FAIL', f'call {i}: {name} has no mock implementation'))
                continue
            if problem:
                out.append(check('signatures', 'UNVERIFIED',
                                 f'call {i}: {name} defined with different signatures', problem))
                continue
            out.append(check('signatures', 'PASS', f'call {i}: {name} has a mock implementation'))
            entries, kwargs = signature(method)
        required = {k for k, req, _ in entries if req}
        allowed = {k for k, _, _ in entries}
        missing = required - inputs.keys()
        extra = set() if kwargs else set(inputs) - allowed
        out.append(check('signatures', 'FAIL' if missing or extra else 'PASS', f'call {i}: {name} argument names',
                         f'missing={sorted(missing)} extra={sorted(extra)}'))
        for key, _, ann in entries:
            if key not in inputs or ann is None:
                continue
            valid = annotation_matches(inputs[key], ann, typed_dicts)
            out.append(check('signatures', 'UNVERIFIED' if valid is None else ('PASS' if valid else 'FAIL'),
                             f'call {i}: {name}.{key} argument type', f'value type={type(inputs[key]).__name__}'))
    return out


def task_id_check(task, domain, seen_ids):
    task_id = task.get('test_case_id')
    if not isinstance(task_id, str) or not task_id:
        return check('references', 'FAIL', 'task ID present')
    if task_id in seen_ids:
        return check('references', 'FAIL', 'task ID unique across benchmark', f'also in {seen_ids[task_id]}')
    seen_ids[task_id] = domain
    return check('references', 'PASS', 'task ID unique across benchmark')


def match_reference(task, tests):
    """Match a JSON task to its Python test: by task ID first, then by title."""
    by_id = [t for t in tests if t['test_id'] is not None and t['test_id'] == task.get('test_case_id')]
    by_title = [t for t in tests if t['title'] is not None and t['title'] == task.get('title')]
    for how, matches in (('task ID', by_id), ('title', by_title)):
        if len(matches) == 1:
            return matches[0], check('references', 'PASS', f'Python reference test found by {how}',
                                     matches[0]['cls'])
        if len(matches) > 1:
            return None, check('references', 'FAIL', f'several Python reference tests share this {how}',
                               ', '.join(t['cls'] for t in matches))
    return None, check('references', 'FAIL', 'Python reference test found', 'no match by task ID or title')


def is_reference_key(key, config):
    return key.endswith('_id') or key in config['reference_keys']


def provenance_checks(task, calls, responses, config):
    """Every ID used in a call must come from the task input or an earlier tool result."""
    out = []
    source = task.get('representative_input')
    from_input = set(scalar_values(source)) if isinstance(source, dict) else set()
    from_tools, origin_unknown = set(), ''
    for i, (call, response) in enumerate(zip(calls, responses), 1):
        if not isinstance(call, dict):
            continue
        inputs = call.get('tool_inputs')
        for key, value in (inputs.items() if isinstance(inputs, dict) else ()):
            if not is_reference_key(key, config):
                continue
            for v in (value if isinstance(value, list) else [value]):
                if not isinstance(v, (str, int, float, bool)):
                    continue
                label, evidence = f'call {i}: {key} origin', f'value={v!r}'
                if v in from_input:
                    out.append(check('references', 'PASS', label, f'{evidence}; from task input'))
                elif v in from_tools:
                    out.append(check('references', 'PASS', label, f'{evidence}; from earlier tool result'))
                elif origin_unknown:
                    out.append(check('references', 'UNVERIFIED', label, f'{evidence}; {origin_unknown}'))
                else:
                    out.append(check('references', 'FAIL', label,
                                     f'{evidence}; not in task input or any earlier tool result'))
        if call.get('name') == 'HUMAN_IN_THE_LOOP':
            origin_unknown = origin_unknown or f'user may supply values after call {i}'
        elif response is UNKNOWN:
            origin_unknown = origin_unknown or f'response of call {i} could not be predicted'
        elif response is not None:
            from_tools.update(scalar_values(response))
    return out


def output_checks(task, calls, responses, config):
    """Each expected value must be producible by a tool called up to that point.

    PASS: some tool call up to that point returns exactly the expected value.
    FAIL: every tool call up to that point was predicted and none returns it.
    UNVERIFIED: anything else.
    """
    generic = set(config['generic_fields'])
    expected = []
    milestones = task.get('milestones')
    for i, m in enumerate(milestones if isinstance(milestones, list) else [], 1):
        if isinstance(m, dict) and isinstance(m.get('expected_state'), dict):
            step = m['step'] if type(m.get('step')) is int else i
            expected += [(f'milestone {i}', p, v, step) for p, v in leaves(m['expected_state'])]
    outcome = task.get('expected_success_outcome')
    if isinstance(outcome, dict) and isinstance(outcome.get('key_outputs'), dict):
        expected += [('final output', p, v, len(calls)) for p, v in leaves(outcome['key_outputs'])]
    if not any(isinstance(r, dict) for r in responses):
        return [check('output_consistency', 'UNVERIFIED', 'no tool responses could be predicted')]
    out = []
    for location, path, value, window in expected:
        label = f'{location}.{path}'
        in_window = [(i, calls[i - 1].get('name'), r) for i, r in enumerate(responses, 1)
                     if i <= window and r is not None]
        known = [(i, n, r) for i, n, r in in_window if isinstance(r, dict)]
        unknown = [i for i, _, r in in_window if r is UNKNOWN]
        leaf = path.rsplit('.', 1)[-1]
        candidates = [(i, n, get_path(r, path)) for i, n, r in known if get_path(r, path) is not MISSING]
        if candidates:
            how = 'full path'
        elif '.' not in path and leaf in generic:
            out.append(check('output_consistency', 'UNVERIFIED', label, 'generic field, producer ambiguous'))
            continue
        else:
            candidates = [(i, n, r[leaf]) for i, n, r in known if leaf in r]
            how = 'field name'
        matching = [(i, n) for i, n, v in candidates if v == value]
        if matching:
            i, n = matching[0]
            out.append(check('output_consistency', 'PASS', label,
                             f'expected={value!r}; produced by {n} (call {i}), matched on {how}'))
        elif candidates and not unknown:
            seen = '; '.join(f'{n} (call {i}) returns {v!r}' for i, n, v in candidates)
            out.append(check('output_consistency', 'FAIL', label, f'expected={value!r}; {seen}'))
        elif candidates:
            out.append(check('output_consistency', 'UNVERIFIED', label,
                             f'expected={value!r}; no predicted match, unpredicted calls {unknown}'))
        else:
            out.append(check('output_consistency', 'UNVERIFIED', label, 'no predicted tool returns this field'))
    return out or [check('output_consistency', 'UNVERIFIED', 'no expected outputs to compare')]


# ---------------------------------------------------------------- scoring

def category_status(checks, category):
    counts = Counter(c['status'] for c in checks if c['category'] == category)
    return 'FAIL' if counts['FAIL'] else ('PASS' if counts['PASS'] else 'UNVERIFIED')


def score_task(checks):
    statuses = {c: category_status(checks, c) for c in CATEGORIES}
    scorable = [c for c in CATEGORIES if statuses[c] != 'UNVERIFIED']
    passed = sum(statuses[c] == 'PASS' for c in scorable)
    counts = Counter(c['status'] for c in checks)
    return dict(D_i=round(passed / len(scorable), 4) if scorable else None,
                V_i=round(len(scorable) / len(CATEGORIES), 4),
                categories=statuses, checks_passed=counts['PASS'],
                checks_failed=counts['FAIL'], checks_unverified=counts['UNVERIFIED'])


def summarize(tasks):
    audited = len(tasks)
    scores = [t['D_i'] for t in tasks if t['D_i'] is not None]
    out = dict(tasks_audited=audited, tasks_scorable=len(scores), tasks_unscorable=audited - len(scores),
               C_det=round(sum(scores) / len(scores), 4) if scores else None,
               Cov_det=round(len(scores) / audited, 4) if audited else None,
               tasks_D_1=sum(s == 1 for s in scores), tasks_D_0=sum(s == 0 for s in scores))
    for c in CATEGORIES:
        statuses = [t['categories'][c] for t in tasks]
        p, f = statuses.count('PASS'), statuses.count('FAIL')
        out[f'{c}_pass_rate'] = round(p / (p + f), 4) if p + f else None
        out[f'{c}_coverage'] = round((p + f) / audited, 4) if audited else None
    return out


# ---------------------------------------------------------------- domain audit

def discover_tasks(data):
    """Return (task candidates, warnings) from the known test_cases.json layouts."""
    found, warnings = [], []
    if isinstance(data, list):
        return data, warnings
    if not isinstance(data, dict):
        return [], ['test_cases.json is neither an object nor a list']
    for w, workflow in enumerate(data.get('workflows') or [], 1):
        if isinstance(workflow, dict) and isinstance(workflow.get('test_cases'), list):
            found += workflow['test_cases']
        else:
            warnings.append(f'workflow {w} has no test_cases list')
    if isinstance(data.get('test_cases'), list):
        found += data['test_cases']
    if not found and not warnings:
        warnings.append('no tasks under workflows[*].test_cases or test_cases')
    return found, warnings


def audit_domain(domain, seen_ids, base_config):
    report = dict(domain=domain.name, tasks=[], warnings=[], tasks_discovered=0, tasks_skipped=0)
    config = load_config(domain, base_config)
    try:
        data = json.loads((domain / 'test_cases.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        report['warnings'].append(f'test_cases.json unreadable: {exc}')
        return report
    candidates, warnings = discover_tasks(data)
    report['warnings'] += warnings
    report['tasks_discovered'] = len(candidates)
    py_path = domain / 'test_cases.py'
    tests, tool_defs, typed_dicts = [], {}, {}
    if py_path.exists():
        try:
            tests, tool_defs, typed_dicts = source_model(py_path, config['python_id_fields'])
        except SyntaxError as exc:
            report['warnings'].append(f'test_cases.py has a syntax error: {exc}')
    else:
        report['warnings'].append('test_cases.py missing: every task will fail the reference test check')
    declared, declared_problem = load_declared_tools(domain)
    if declared_problem:
        report['warnings'].append(f'tool declarations not checked: {declared_problem}')
    else:
        undeclared = sorted(set(tool_defs) - declared)
        unmocked = sorted(declared - set(tool_defs))
        if undeclared:
            report['warnings'].append(f'mocked but not declared in agent definition: {undeclared}')
        if unmocked:
            report['warnings'].append(f'declared but not mocked: {unmocked}')

    for task in candidates:
        if not isinstance(task, dict):
            report['tasks_skipped'] += 1
            continue
        checks = schema_checks(task)
        checks.append(task_id_check(task, domain.name, seen_ids))
        reference, match_check = match_reference(task, tests)
        checks.append(match_check)
        if reference is None:
            checks.append(check('signatures', 'FAIL', 'no Python reference test, calls cannot be validated'))
            checks.append(check('output_consistency', 'UNVERIFIED', 'no Python reference test'))
        elif reference['calls'] is None:
            checks.append(check('signatures', 'UNVERIFIED', 'expected_tool_calls is not a plain literal list'))
            checks.append(check('output_consistency', 'UNVERIFIED', 'expected_tool_calls is not a plain literal list'))
        else:
            calls = reference['calls']
            responses = predict_responses(calls, tool_defs)
            checks += signature_checks(calls, tool_defs, typed_dicts, declared, declared_problem)
            checks += provenance_checks(task, calls, responses, config)
            checks += output_checks(task, calls, responses, config)
        report['tasks'].append(dict(domain=domain.name, task_id=task.get('test_case_id'), title=task.get('title'),
                                     reference_test=reference['cls'] if reference else None,
                                     **score_task(checks), checks=checks))
    report.update(summarize(report['tasks']))
    return report


def log_line(name, discovered, audited, skipped, unscorable):
    return f'{name}: Discovered: {discovered} | Audited: {audited} | Skipped: {skipped} | Unscorable: {unscorable}'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=Path('audit_results'))
    parser.add_argument('--config', type=Path, help='JSON file overriding DEFAULT_CONFIG for all domains')
    args = parser.parse_args()

    base_config = dict(DEFAULT_CONFIG)
    if args.config:
        base_config.update(json.loads(args.config.read_text(encoding='utf-8')))
    if (args.data_dir / 'test_cases.json').exists():
        domains = [args.data_dir]
    else:
        domains = sorted(p for p in args.data_dir.iterdir() if p.is_dir() and (p / 'test_cases.json').exists())
    if not domains:
        parser.error('No domain folders with test_cases.json found')

    seen_ids = {}  # Shared across domains: task IDs must be unique benchmark-wide.
    reports = [audit_domain(p, seen_ids, base_config) for p in domains]
    tasks = [t for r in reports for t in r['tasks']]
    overall = dict(domain='ALL', tasks_discovered=sum(r['tasks_discovered'] for r in reports),
                   tasks_skipped=sum(r['tasks_skipped'] for r in reports), **summarize(tasks))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'audit_details.json').write_text(
        json.dumps({'overall': overall, 'domains': reports}, indent=2, default=str), encoding='utf-8')

    task_rows = [{**{k: v for k, v in t.items() if k not in ('checks', 'categories')}, **t['categories']}
                 for t in tasks]
    task_cols = ['domain', 'task_id', 'title', 'reference_test', 'D_i', 'V_i', *CATEGORIES,
                 'checks_passed', 'checks_failed', 'checks_unverified']
    domain_cols = ['domain', 'tasks_discovered', 'tasks_audited', 'tasks_skipped', 'tasks_scorable',
                   'tasks_unscorable', 'C_det', 'Cov_det', 'tasks_D_1', 'tasks_D_0',
                   *(f'{c}_{s}' for c in CATEGORIES for s in ('pass_rate', 'coverage'))]
    for filename, rows, cols in (('task_scores.csv', task_rows, task_cols),
                                 ('domain_scores.csv', [*reports, overall], domain_cols)):
        with (args.output_dir / filename).open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=cols, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)

    for r in reports:
        print(log_line(r['domain'], r['tasks_discovered'], r.get('tasks_audited', 0),
                       r['tasks_skipped'], r.get('tasks_unscorable', 0)))
        for warning in r['warnings']:
            print(f'  WARNING: {warning}')
    print(log_line('ALL', overall['tasks_discovered'], overall['tasks_audited'],
                   overall['tasks_skipped'], overall['tasks_unscorable']))
    print(f"C_det={overall['C_det']}  Cov_det={overall['Cov_det']}")
    for c in CATEGORIES:
        print(f"  {c:<20} pass_rate={overall[f'{c}_pass_rate']}  coverage={overall[f'{c}_coverage']}")
    print(f'Results: {args.output_dir}')


if __name__ == '__main__':
    main()