"""Load immutable benchmark inputs without importing an agent or generating runs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

SUPPORTED_REVISION = "5ade54e282a4555e4d6c52d6b9b861ea8872afa6"
DOMAINS = ("retail", "airline", "telecom")


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def revision(root):
    if not (Path(root) / ".git").exists():
        return None
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def load_dataset(root, domain="retail", split="base", task_ids=None, limit=None):
    """Return a harness manifest; accept checkout, data, or data/tau2 roots.

    Task definitions remain raw so bad task records reach the schema checker.
    Shared assets are referenced by absolute path and hash, not duplicated in
    every task. A manifest therefore requires those assets to remain available.
    """
    if domain not in DOMAINS:
        raise ValueError(f"Unsupported domain: {domain}")
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("limit must be a positive integer")
    root = Path(root).resolve()
    candidates = (root / "data" / "tau2", root / "tau2", root)
    data = next((p for p in candidates if (p / "domains" / domain).is_dir()), None)
    if data is None:
        raise FileNotFoundError(f"No τ² {domain} data below {root}")
    directory = data / "domains" / domain
    names = ["tasks.json", "split_tasks.json"]
    names += (["db.toml", "user_db.toml", "main_policy.md", "tech_support_manual.md"]
              if domain == "telecom" else ["db.json", "policy.md"])
    sources = {name: {"path": str(directory / name), "sha256": fingerprint(directory / name)}
               for name in names}
    checkout = data.parent.parent
    rev = revision(checkout)
    records = json.loads((directory / "tasks.json").read_text())
    if not isinstance(records, list):
        raise ValueError("tasks.json must contain a list")
    splits = json.loads((directory / "split_tasks.json").read_text())
    if split is not None and split not in splits:
        raise ValueError(f"Unknown split {split!r}; available: {list(splits)}")
    selected = set(splits[split]) if split is not None else None
    requested = set(task_ids) if task_ids is not None else None
    if requested is not None and not requested:
        raise ValueError("task_ids must not be empty")
    source = {"benchmark": "tau2", "domain": domain, "revision": rev,
              "supported_revision": SUPPORTED_REVISION, "sources": sources}
    tasks, seen, found = [], set(), set()
    for index, record in enumerate(records):
        raw_id = record.get("id") if isinstance(record, dict) else None
        # Missing/invalid IDs are retained as failed schema records.
        key = raw_id if isinstance(raw_id, str) else f"malformed-record-{index}"
        if key in seen:
            raise ValueError(f"Duplicate task ID: {key}")
        seen.add(key)
        if isinstance(raw_id, str) and selected is not None and raw_id not in selected:
            continue
        if requested is not None and key not in requested:
            continue
        found.add(key)
        tasks.append({"id": key, "task": {"source": deepcopy(source),
                                           "definition": deepcopy(record)}})
    if requested is not None and requested - found:
        raise ValueError(f"Task IDs absent from selected split: {sorted(requested - found)}")
    if limit is not None:
        tasks = tasks[:limit]
    if not tasks:
        raise ValueError("Task selection is empty")
    return {"dataset": f"tau2/{domain}", "subject": "reference_tasks",
            "split": split, "task_ids": [t["id"] for t in tasks], "sources": source,
            "tasks": tasks, "mutations": []}
