"""Fresh real-tool environments backed by verified, read-only source assets."""

from copy import deepcopy
from functools import lru_cache
import importlib
import json
import os
from pathlib import Path

from .adapter import SUPPORTED_REVISION, fingerprint, revision


def dependencies():
    # Importing tau2 also imports LiteLLM. Keep its model-price lookup offline.
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    try:
        import tau2
        from jsonschema import Draft202012Validator
    except ImportError as error:
        raise RuntimeError("Install the optional tau2 extra; see validation/README.md") from error
    return tau2, Draft202012Validator


@lru_cache(maxsize=16)
def context(serialized_source):
    """Cache only a pristine environment and schemas, never evaluated state."""
    source = json.loads(serialized_source)
    tau2, validator = dependencies()
    installed_root = Path(tau2.__file__).resolve().parents[2]
    installed_revision = revision(installed_root)
    if installed_revision is None:
        from importlib.metadata import distribution
        direct = distribution("tau2").read_text("direct_url.json")
        installed_revision = (json.loads(direct).get("vcs_info", {}).get("commit_id")
                              if direct else None)
    if installed_revision != SUPPORTED_REVISION:
        raise RuntimeError(f"τ² runtime revision {installed_revision!r} differs from pinned "
                           f"{SUPPORTED_REVISION}; install the pinned extra")
    if source.get("revision") not in (None, installed_revision):
        raise RuntimeError("Benchmark checkout and installed tool revisions differ")
    files = source["sources"]
    for entry in files.values():
        if fingerprint(entry["path"]) != entry["sha256"]:
            raise ValueError(f"Source hash mismatch: {entry['path']}")
    domain = source["domain"]
    if domain not in ("retail", "airline", "telecom"):
        raise ValueError(f"Unsupported domain: {domain}")
    from tau2.environment.environment import Environment
    models = importlib.import_module(f"tau2.domains.{domain}.data_model")
    tools = importlib.import_module(f"tau2.domains.{domain}.tools")
    if domain == "telecom":
        from tau2.domains.telecom.environment import TelecomEnvironment
        from tau2.domains.telecom.user_data_model import TelecomUserDB
        from tau2.domains.telecom.user_tools import TelecomUserTools
        env = TelecomEnvironment(
            "telecom", "\n".join(Path(files[n]["path"]).read_text()
                                  for n in ("main_policy.md", "tech_support_manual.md")),
            tools.TelecomTools(models.TelecomDB.load(files["db.toml"]["path"])),
            TelecomUserTools(TelecomUserDB.load(files["user_db.toml"]["path"])),
        )
    else:
        model = models.RetailDB if domain == "retail" else models.FlightDB
        toolkit = tools.RetailTools if domain == "retail" else tools.AirlineTools
        env = Environment(domain, Path(files["policy.md"]["path"]).read_text(),
                          toolkit(model.load(files["db.json"]["path"])))
    validators = {}
    for role, kit in (("assistant", env.tools), ("user", env.user_tools)):
        validators[role] = {}
        if kit:
            for name, tool in kit.get_tools().items():
                schema = deepcopy(tool.openai_schema["function"]["parameters"])
                schema["additionalProperties"] = False
                validator.check_schema(schema)
                validators[role][name] = validator(schema)
    implementation = importlib.import_module(f"tau2.domains.{domain}.tools")
    return env, validators, {"revision": installed_revision, "version": "1",
                            "tool_implementation_sha256": fingerprint(implementation.__file__)}


def fresh_environment(source):
    env, validators, metadata = context(json.dumps(source, sort_keys=True))
    return deepcopy(env), validators, deepcopy(metadata)


def state(env):
    return {"agent": env.tools.db.model_dump(mode="json") if env.tools and env.tools.db else None,
            "user": env.user_tools.db.model_dump(mode="json")
            if env.user_tools and env.user_tools.db else None}


def differences(before, after, path=(), limit=20):
    """Bounded state differences; final-state hashes retain full-state identity."""
    changes = []

    def walk(a, b, p):
        if a == b or len(changes) >= limit:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() | b.keys()):
                if key not in a or key not in b:
                    changes.append({"path": list((*p, key)), "before": a.get(key), "after": b.get(key)})
                else:
                    walk(a[key], b[key], (*p, key))
                if len(changes) >= limit:
                    break
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for i, (left, right) in enumerate(zip(a, b)):
                walk(left, right, (*p, i))
        else:
            changes.append({"path": list(p), "before": a, "after": b})
    walk(before, after, path)
    return {"changes": changes, "limit": limit, "possibly_truncated": len(changes) == limit}
