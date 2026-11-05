# Correctness evaluation and evaluator validation

The operational evaluator checks task structure, tool signatures, entity references,
and real tool replay. The validation harness deliberately corrupts tasks to test
whether that evaluator detects the intended mistakes. An evaluator-validation pass
is separate from the dataset's correctness score and from task success.

## Quick start

The original demo needs no benchmark installation:

```bash
.venv/bin/python -m validation.correctness_checker --demo --output output/demo-validation
```

Every completed command writes `report.md`, `report.json`, `summary.csv`, and
`manifest.json`, then prints a compact terminal summary. Open **report.md** for
readable results; JSON contains the complete per-task evidence. Existing output
files in the chosen directory are replaced; use separate directories for runs you
want to compare. No agent trajectories are generated and no LLM calls are made.

## Install the optional benchmark integration

Run from the repository root with Python 3.13:

```bash
uv sync --extra tau2
```

The extra pins τ²-bench to commit
`5ade54e282a4555e4d6c52d6b9b861ea8872afa6` and adds JSON Schema validation.
`audioop-lts` supplies the Python 3.13 compatibility module imported by upstream.
Benchmark assets are loaded explicitly from a checkout or data directory:

```bash
.venv/bin/python -m evaluation.tau2 \
  --benchmark-root /path/to/tau2-bench \
  --domain retail --output output/retail-baseline

.venv/bin/python -m evaluation.tau2 \
  --benchmark-root /path/to/tau2-bench \
  --domain retail --validate-corruptions --output output/retail-validation

.venv/bin/python -m evaluation.tau2 \
  --benchmark-root /path/to/tau2-bench \
  --controls --validate-corruptions --output output/retail-controls
```

`--benchmark-root` accepts a checkout, its `data` directory, or its `data/tau2`
directory. `--split base` is the default. Use `--task-ids 0 1`, `--limit 10`,
`--rates 0 .1 .25 .5 1`, and `--seed 42` for selection and experiments.
The base splits contain **114 retail, 50 airline, and 114 telecom tasks**. Telecom
also offers the larger `--split full` collection of 2,285 tasks; base is the default
for comparable validation runs. All three domains support the same seven campaigns
and `--controls` workflow. Telecom retains assistant/user tool actions and
synchronizes the two environments after calls.

Run the other two domains end to end:

```bash
.venv/bin/python -m evaluation.tau2 --benchmark-root /path/to/tau2-bench \
  --domain airline --validate-corruptions --output output/tau2-airline-validation
.venv/bin/python -m evaluation.tau2 --benchmark-root /path/to/tau2-bench \
  --domain telecom --validate-corruptions --output output/tau2-telecom-validation
.venv/bin/python -m evaluation.tau2 --benchmark-root /path/to/tau2-bench \
  --domain airline --controls --validate-corruptions --output output/tau2-airline-controls
.venv/bin/python -m evaluation.tau2 --benchmark-root /path/to/tau2-bench \
  --domain telecom --controls --validate-corruptions --output output/tau2-telecom-controls
```

The runtime must match the pinned code revision. Asset paths and SHA-256 hashes
are retained in the manifest; installed tool implementation hashes are retained
in results. Shared benchmark files must remain available to replay a saved
manifest. Inputs are not silently repaired, relabeled, or altered on disk.

## What the four checks mean

| Check | Evidence |
| --- | --- |
| `schema` | Strict upstream task/action models, nonempty IDs, unique action IDs, and valid initialization message pairing. |
| `signatures` | Actual requestor-specific tool schemas; required/unexpected arguments, primitive/nested types, and declared enums. Values are not coerced. |
| `references` | Explicit domain mappings against the current database, including ownership and container relationships. No generic assumption that every `_id` is an existing entity. |
| `output_consistency` | Real execution of every reference call, including reads; tool errors and executable preconditions; recorded-output comparisons when supplied. |

Every evaluation starts from a pristine database copy. Initialization data,
initialization functions, and initialization message history are applied once,
then reference actions execute in order. Signatures are checked before replay;
replay stops at the first invalid reference, failed call, or output mismatch.
The report includes action IDs, output previews/hashes, final-state hashes, and
bounded state differences. Known benchmark `ValueError`/`AssertionError` tool
failures are task defects; unexpected exceptions are experiment errors.

A check is 0 or 1. `null` means unavailable/inapplicable, including checks blocked
by an earlier defect; coverage explains the reason. Task scores average applicable
checks, and dataset scores average tasks. Passing all applicable checks with
incomplete coverage is distinct from being fully evaluated across all four checks.
An empty action list is valid structure, with no applicable call-based checks.

This is an operational reliability metric. It does not prove that reference actions
satisfy prose instructions, enforce conversational confirmation/policy requirements,
or constitute the only acceptable solution. Upstream reward and replay alone are
insufficient here because they may skip reads/unknown tools or continue after errors.

## Controlled corruptions and clean labels

Campaigns cover malformed actions, unknown tools, wrong argument types, missing
and unexpected arguments, nonexistent entities, and broken preconditions.
Precondition defects follow the real tool implementation: repeat a consumed retail
order operation; attempt an airline baggage update with an existing certificate
(a prohibited payment method for updates); or request a telecom refill of 0 GB.
Airline cancellation itself has no repeat-cancellation guard, so repeating it is
not treated as a known executable defect. Every generated mutation records its
construction rule. For no-argument-only trajectories, type and missing-argument
campaigns append a malformed parameterized read instead of mislabeling an extra
argument. Reference campaigns still exclude tasks with no passing entity check.
Rates select nested subsets of **eligible tasks**, not individual calls. One
mutation per task is applied in each campaign. The JSON and CSV retain requested,
effective-eligible, and effective-dataset rates, including rounding effects.
Baseline failures remain in the dataset average. Mutations must match their
independently declared full check vectors and expected partial-credit score changes;
aggregate agreement cannot hide detection in the wrong check.

`--controls` constructs 20 tasks for the selected domain: retail cancellations,
airline paid baggage updates across real reservations, or telecom roaming changes
across owned lines and distinct initial device settings. Airline controls assert
the baggage counts and $50 payment; telecom controls assert both the line and device
roaming settings, synchronization, and preservation of airplane/data settings.
Their labels derive from the tool contracts and independent final-state assertions,
not mutated evaluator results. These are
**constructed controls, not human-reviewed labels for original benchmark tasks**.
Each core campaign has 20 eligible controls. Original tasks are not presumed clean.
False-positive rates are unavailable without clean labels.

To attach human-reviewed labels to selected original tasks, use `--labels labels.json`:

```json
{
  "0": {"expected_pass": true, "reviewer": "Reviewer name", "notes": "Reviewed operational checks against source state"}
}
```

Unconstructible mutations and baseline target-check failures are listed as exclusions.
A named campaign that never exercises a corruption makes validation inconclusive.
At 0% corruption, detection is **Not evaluated**, not 0%. False-positive denominators
contain only labeled clean tasks left uncorrupted at that rate. The terminal's
campaign detection counts aggregate corrupted evaluations across rates, so a task
can contribute more than once.

## Separate outcome evidence

Reference outcomes are checked only against independently supplied executable
expectations: upstream `env_assertions` or payload assertions such as:

```json
{"expected_final_state": [{"path": ["agent", "orders", "#W123", "status"], "value": "cancelled"}]}
```

Missing expectations, blocked replay, communication requirements without a dialogue,
and natural-language assertions are explicitly uncovered. Retail reference tasks
provide no independent environment assertions, so their outcomes normally read
**Not evaluated**. Outcome results do not change the four-check score. Comparing
a reference replay with a target derived from that same replay is never used as
proof that its task was solved.

## Existing recorded agent runs

This separate workflow evaluates existing half-duplex simulations and reports
agent-run reliability/outcomes independently from dataset-quality scores:

```bash
.venv/bin/python -m evaluation.tau2.recorded \
  --benchmark-root /path/to/tau2-bench --domain retail \
  --results /path/to/results.json --limit 5 --output output/recorded-runs
```

Embedded task definitions are preserved. Task drift against the selected benchmark
is rejected before replay. To intentionally replay embedded historical definitions
on the supplied snapshot, use `--allow-task-drift`; mismatches are retained in the
report. Historical database identity is unverified unless separately established.
Full-duplex tick trajectories are rejected. Tool-result pairing and recorded outputs
are checked. The initial-history prefix is consumed exactly once.

For candidate outcomes, a separate fresh reference replay supplies the target DB
state. DB, executable environment assertions, deterministic communication checks,
and normal termination can be checked; unsupported reward components remain
uncovered. This fail-fast offline workflow is not an official leaderboard regrade
and does not silently invoke an LLM for semantic requirements.

## Synthetic datasets

The parked static reader has been restored as `evaluation.synthetic`. It parses
Python fixtures with AST, without importing their LLM-initializing base classes:

```bash
.venv/bin/python -m evaluation.synthetic \
  --dataset data/banking_customer_onboarding --validate-corruptions \
  --output output/synthetic-banking
```

All seven domain readers are supported. Reports explicitly label this as **static
consistency only**: no real entity database, tool replay, or independent outcome
proof is available. Their scores have different coverage from τ² and must not be
presented as directly equivalent. Existing JSON/Python ID inconsistencies are
reported rather than silently fixed.

## External evaluator compatibility

```bash
.venv/bin/python -m validation.correctness_checker \
  --input manifest.json --evaluator module:function --output output/external-validation
```

Contract: `evaluate(task: dict) -> {"checks": {category: score}}`. Additional
JSON-serializable evidence is preserved. Deterministic categories are `schema`,
`signatures`, `references`, `output_consistency`. Optional external LLM mode keeps
its existing 0/0.5/1 rubric and separate category names; no judge is implemented here.

## Verification and exit codes

```bash
.venv/bin/python -m unittest discover -s validation -p 'test_*.py'
TAU2_BENCHMARK_ROOT=/path/to/tau2-bench \
  .venv/bin/python -m unittest discover -s validation -p 'test_*.py'
```

Without `TAU2_BENCHMARK_ROOT`, real-tool tests are explicitly skipped; harness,
reporting, adapter, and synthetic reader tests still run. The integration suite
checks real reads/writes, isolated state, controlled corruptions, initialization,
strict types, ownership, independent outcomes, recorded runs, and version/data drift.

Exit codes: **0** validation passed or baseline-only evaluation completed;
**1** validation failed; **2** experiment error; **3** validation inconclusive.
A baseline-only report says `NOT RUN` for validation and is not an assertion that
all tasks passed. Errors print a concise cause and write `error.json` when possible;
existing completed reports in a reused directory may belong to an earlier attempt.
