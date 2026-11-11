"""Static, source-backed inputs for the pinned τ-bench v1.0.1 judge.

This module never imports τ-bench or executes its tools or initialization code.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib


BENCHMARK_TAG = "v1.0.1"
BENCHMARK_COMMIT = "fc0055dc4e0a316c3f83133267fbd6faaa770992"
DOMAINS = ("airline", "retail", "telecom")
BASE_COUNTS = {"airline": 50, "retail": 114, "telecom": 114}
WORKSPACE = Path(__file__).resolve().parents[2]
DEFAULT_TAU2_DIR = WORKSPACE / "t-bench_data" / "tau2-bench"
DEFAULT_OUTPUT_DIR = WORKSPACE / "llm_t-bench_results"
ADAPTER_VERSION = "tau2-static-1.0"


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"Cannot verify τ-bench checkout at {root}: {exc}") from exc


class StaticToolkit:
    """Extract documented tools and referenced implementation dependencies via AST."""

    def __init__(self, source: str, path: str, class_name: str):
        self.path = path
        tree = ast.parse(source, filename=path)
        cls = next((n for n in tree.body if isinstance(n, ast.ClassDef)
                    and n.name == class_name), None)
        if cls is None:
            raise ValueError(f"Missing class {class_name} in {path}")
        self.methods = {
            n.name: n for n in cls.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.definitions = {}
        for name, method in self.methods.items():
            decorators = [ast.unparse(d) for d in method.decorator_list]
            if not any(d.startswith("is_tool(") for d in decorators):
                continue
            self.definitions[name] = {
                "signature": ast.unparse(method.args),
                "returns": ast.unparse(method.returns) if method.returns else None,
                "docstring": ast.get_docstring(method),
                "decorators": decorators,
                "source": f"{path}:{method.lineno}",
            }
        if not self.definitions:
            raise ValueError(f"No documented tools in {path}")
        self.class_context = "\n".join(
            ast.unparse(n) for n in cls.body
            if isinstance(n, (ast.Assign, ast.AnnAssign))
        )
        self.module_context = "\n".join(
            ast.unparse(n) for n in tree.body
            if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.Assign, ast.AnnAssign))
            and n is not cls
        )

    def implementations(self, names: set[str]) -> dict:
        """Include referenced functions and their self.method/property dependencies."""
        pending = sorted(names)
        selected = {}
        while pending:
            name = pending.pop()
            if name in selected or name not in self.methods:
                continue
            node = self.methods[name]
            selected[name] = {
                "source": f"{self.path}:{node.lineno}",
                "code": ast.unparse(node),
            }
            pending.extend(
                n.attr for n in ast.walk(node)
                if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                and n.value.id == "self" and n.attr in self.methods
            )
        return dict(sorted(selected.items()))


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def select_initial_records(database: dict, task: dict) -> dict:
    """Select identities mentioned by the task, then close over outgoing ID links.

    No state is simulated. Full selected records are retained, including related
    orders/reservations/products/flights, rather than only the mentioned fields.
    """
    records = {}
    lookup = {}
    identities = {}
    for table, values in database.items():
        if not isinstance(values, dict):
            raise ValueError(f"Expected keyed records for table {table}")
        for key, record in values.items():
            if not isinstance(record, dict):
                raise ValueError(f"Expected object for {table}/{key}")
            location = (table, key)
            records[location] = record
            lookup.setdefault(str(key), set()).add(location)
            tokens = [str(key)]
            name = record.get("name")
            if isinstance(name, dict):
                full_name = " ".join(str(name.get(k, "")) for k in ("first_name", "last_name")).strip()
                if full_name:
                    tokens.append(full_name)
            for field in ("email", "phone_number"):
                if isinstance(record.get(field), str):
                    tokens.append(record[field])
            identities[location] = tokens
    text = "\n".join(_strings(task))
    selected = {
        location for location, tokens in identities.items()
        if any(re.search(r"(?<![\w])" + re.escape(token) + r"(?![\w])", text, re.I)
               for token in tokens)
    }
    pending = list(selected)
    while pending:
        location = pending.pop()
        for value in _strings(records[location]):
            for linked in lookup.get(value, ()):
                if linked not in selected:
                    selected.add(linked)
                    pending.append(linked)
    extracted = {table: {} for table in database}
    for table, key in sorted(selected):
        extracted[table][key] = deepcopy(records[(table, key)])
    return {
        "records": extracted,
        "selection_method": "Task-mentioned record IDs, full names, emails, or phone numbers; transitive outgoing ID links.",
        "selected_counts": {k: len(v) for k, v in extracted.items()},
        "total_counts": {k: len(v) for k, v in database.items()},
        "limitations": [
            "This is a database extract, not a complete database or executed initial state.",
            "Records not reachable by the documented selection rule are omitted; absence from this extract does not prove nonexistence.",
        ],
    }


class TauBenchAdapter:
    """Load official task selections and sufficient traceable static context."""

    def __init__(self, root: Path = DEFAULT_TAU2_DIR, domain: str | None = None,
                 split: str = "base", limit: int | None = None):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"τ-bench directory not found: {self.root}")
        self.commit = _git(self.root, "rev-parse", "HEAD")
        tag_commit = _git(self.root, "rev-parse", f"{BENCHMARK_TAG}^{{commit}}")
        if self.commit != BENCHMARK_COMMIT or tag_commit != BENCHMARK_COMMIT:
            raise ValueError(f"Expected {BENCHMARK_TAG} at {BENCHMARK_COMMIT}; checkout is {self.commit}")
        if _git(self.root, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError("τ-bench has tracked modifications; restore the pinned source before evaluating")
        if domain is not None and domain not in DOMAINS:
            raise ValueError(f"Unsupported τ-bench domain: {domain}; choose {DOMAINS}")
        if limit is not None and limit < 1:
            raise ValueError("τ-bench --limit must be positive")
        self.split = split
        self.sources = {}
        self.contexts = {}
        self.tasks = []
        self.selected_counts = {}
        for name in DOMAINS if domain is None else (domain,):
            self._load_domain(name)
        if limit is not None:
            self.tasks = self.tasks[:limit]
        if not self.tasks:
            raise ValueError("τ-bench task selection is empty")

    def _read(self, relative: str) -> str:
        path = self.root / relative
        try:
            raw = path.read_bytes()
            value = raw.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"Cannot read required τ-bench source {path}: {exc}") from exc
        if not value.strip():
            raise ValueError(f"Empty required τ-bench source: {path}")
        self.sources[relative] = hashlib.sha256(raw).hexdigest()
        return value

    def _load_domain(self, domain: str):
        data = f"data/tau2/domains/{domain}"
        src = f"src/tau2/domains/{domain}"
        tasks = json.loads(self._read(f"{data}/tasks.json"))
        splits = json.loads(self._read(f"{data}/split_tasks.json"))
        if not isinstance(tasks, list) or self.split not in splits:
            raise ValueError(f"Invalid task list or unknown split {self.split!r} for {domain}")
        ids = splits[self.split]
        if not isinstance(ids, list) or not all(isinstance(i, str) and i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError(f"Invalid or duplicate split IDs in {domain}/{self.split}")
        seen = set()
        for task in tasks:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str) or not task["id"]:
                raise ValueError(f"Missing/invalid task ID in {domain}")
            if task["id"] in seen:
                raise ValueError(f"Duplicate task ID {domain}/{task['id']}")
            seen.add(task["id"])
        if set(ids) - seen:
            raise ValueError(f"Split refers to missing tasks in {domain}: {sorted(set(ids) - seen)}")
        selected = [t for t in tasks if t["id"] in set(ids)]
        if self.split == "base" and len(selected) != BASE_COUNTS[domain]:
            raise ValueError(f"Expected {BASE_COUNTS[domain]} base tasks in {domain}, found {len(selected)}")
        for task in selected:
            scenario = task.get("user_scenario")
            criteria = task.get("evaluation_criteria")
            if not isinstance(scenario, dict) or not scenario.get("instructions") or not isinstance(criteria, dict) or not criteria:
                raise ValueError(f"Missing instructions/evaluation criteria in {domain}/{task['id']}")
            instructions = scenario["instructions"]
            if not isinstance(instructions, (str, dict)) or (isinstance(instructions, dict) and not any(
                    isinstance(instructions.get(key), str) and instructions[key].strip()
                    for key in ("reason_for_call", "task_instructions"))):
                raise ValueError(f"Invalid instructions in {domain}/{task['id']}")
            for field in ("actions", "env_assertions", "communicate_info", "nl_assertions", "reward_basis"):
                if criteria.get(field) is not None and not isinstance(criteria[field], list):
                    raise ValueError(f"Invalid {field} in {domain}/{task['id']}")
            if task.get("initial_state") is not None and not isinstance(task["initial_state"], dict):
                raise ValueError(f"Invalid initial_state in {domain}/{task['id']}")
            initial = task.get("initial_state") or {}
            for key, kind in (("initialization_data", dict), ("initialization_actions", list), ("message_history", list)):
                if initial.get(key) is not None and not isinstance(initial[key], kind):
                    raise ValueError(f"Invalid initial_state.{key} in {domain}/{task['id']}")
        self.selected_counts[domain] = len(selected)
        self.tasks.extend((domain, t) for t in selected)

        policy_names = ("main_policy.md", "tech_support_manual.md") if domain == "telecom" else ("policy.md",)
        policy = {f"{data}/{name}": self._read(f"{data}/{name}") for name in policy_names}
        tool_path = f"{src}/tools.py"
        toolkits = {"assistant": StaticToolkit(self._read(tool_path), tool_path, f"{domain.title()}Tools")}
        supporting = {f"{src}/{name}": self._read(f"{src}/{name}") for name in ("data_model.py", "utils.py", "environment.py")}
        if domain == "telecom":
            user_path = f"{src}/user_tools.py"
            toolkits["user"] = StaticToolkit(self._read(user_path), user_path, "TelecomUserTools")
            supporting[f"{src}/user_data_model.py"] = self._read(f"{src}/user_data_model.py")
            database = tomllib.loads(self._read(f"{data}/db.toml"))
            user_database = tomllib.loads(self._read(f"{data}/user_db.toml"))
        else:
            database = json.loads(self._read(f"{data}/db.json"))
            user_database = None
        if not isinstance(database, dict) or not database:
            raise ValueError(f"Missing/invalid initial database for {domain}")
        for name in ("src/tau2/data_model/tasks.py", "src/tau2/environment/toolkit.py", "src/tau2/environment/db.py"):
            self._read(name)
        self.contexts[domain] = {
            "policy": policy, "toolkits": toolkits, "supporting": supporting,
            "database": database, "user_database": user_database,
        }

    def payload(self, domain: str, original: dict) -> dict:
        context = self.contexts[domain]
        task = deepcopy(original)
        task["test_case_id"] = original["id"]
        instructions = task["user_scenario"]["instructions"]
        label = instructions.get("reason_for_call", "") if isinstance(instructions, dict) else instructions
        task["title"] = f"{domain}: {' '.join(str(label).split())[:180] or original['id']}"
        criteria = deepcopy(task["evaluation_criteria"])
        criteria.setdefault("reward_basis", ["DB", "COMMUNICATE"])
        initial = deepcopy(task.get("initial_state") or {})
        references = {"assistant": set(), "user": set()}
        for action in criteria.get("actions") or []:
            if not isinstance(action, dict) or not isinstance(action.get("arguments"), dict) or not isinstance(action.get("name"), str):
                raise ValueError(f"Malformed reference action in {domain}/{task['id']}")
            actor = action.get("requestor", "assistant")
            if actor not in references:
                raise ValueError(f"Unknown action requestor {actor!r} in {domain}/{task['id']}")
            references[actor].add(action["name"])
        for group in (initial.get("initialization_actions"), criteria.get("env_assertions")):
            for action in group or []:
                if not isinstance(action, dict) or action.get("env_type") not in references or not isinstance(action.get("func_name"), str) or not isinstance(action.get("arguments"), dict):
                    raise ValueError(f"Malformed initialization/assertion in {domain}/{task['id']}")
                references[action["env_type"]].add(action["func_name"])
        tools = {}
        for actor, toolkit in context["toolkits"].items():
            tools[actor] = {
                "available_tools": toolkit.definitions,
                "referenced_implementations": toolkit.implementations(references[actor]),
                "unresolved_references": sorted(references[actor] - toolkit.methods.keys()),
                "class_context": toolkit.class_context,
                "module_context": toolkit.module_context,
            }
        if domain == "telecom":
            db_context = {"records": deepcopy(context["database"]), "selection_method": "Complete small telecom agent database (no truncation).", "limitations": []}
        else:
            db_context = select_initial_records(context["database"], task)
        limitations = [
            "Benchmark initialization actions and reference actions are provided as source evidence only; none have been executed.",
            "The default database and task-specific initialization directives are separate; the database is not a computed post-initialization state.",
            "No target database hash or final state has been computed. Infer documented effects only when supported by supplied source; otherwise use uncertainty.",
        ]
        return {
            "dataset": "tau2", "domain": domain, "workflow": f"{BENCHMARK_TAG}/{self.split}",
            "task": task, "policy": context["policy"], "available_tools": tools,
            "evaluation_criteria": criteria,
            "criteria_semantics": {
                "source": "src/tau2/data_model/tasks.py:EvaluationCriteria",
                "reward_basis": "Only components in reward_basis gate the benchmark reward; other populated checks are diagnostic evidence.",
                "actions": "Reference trajectory describes a target DB outcome when DB is active. Specific actions are required only when ACTION is active; do not assume uniqueness otherwise.",
                "env_assertions": "Expected environment checks with assert_value and arguments; active when ENV_ASSERTION is in reward_basis.",
                "communicate_info": "Required communication when COMMUNICATE is active.",
                "nl_assertions": "Natural-language expectations; gate reward only when NL_ASSERTION is active.",
                "empty_actions": "An empty reference sequence may intentionally leave the database unchanged (for example, refusal). It is not automatically a defect.",
            },
            "initial_state": {"default_agent_database": db_context,
                              "default_user_database": deepcopy(context["user_database"]),
                              "task_directives": initial},
            "supporting_source": context["supporting"],
            "evidence_limitations": limitations + db_context["limitations"],
            "benchmark": {"tag": BENCHMARK_TAG, "commit": self.commit, "split": self.split,
                          "adapter_version": ADAPTER_VERSION, "original_task_id": original["id"]},
        }

    def manifest(self) -> dict:
        return {
            "dataset": "tau2", "benchmark_tag": BENCHMARK_TAG,
            "benchmark_commit": self.commit, "adapter_version": ADAPTER_VERSION,
            "split": self.split, "source_sha256": dict(sorted(self.sources.items())),
            "task_selection": [{"domain": d, "task_id": t["id"]} for d, t in self.tasks],
        }
