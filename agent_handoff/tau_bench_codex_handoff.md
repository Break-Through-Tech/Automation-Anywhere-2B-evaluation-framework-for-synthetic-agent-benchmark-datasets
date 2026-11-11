# Codex Handoff — Add τ-bench v1.0.1 to the Existing LLM Correctness Judge

## Objective

Extend the **existing, working LLM-as-a-Judge correctness evaluation** to evaluate **τ-bench (`tau2-bench`) v1.0.1** tasks in the **airline, retail, and telecom** domains. Reuse the same four-dimensional correctness methodology and the same JSON/CSV reporting pipeline. **Do not break or alter synthetic dataset evaluation.** The user has already completed synthetic evaluation and retained its results, scores, explanations, and evidence for reporting.

This is an assessment of **benchmark task/dataset quality**, **not agent performance**. Do not run τ-bench agents, simulations, evaluation rollouts, or the benchmark's execution infrastructure. Do not implement the separate deterministic correctness evaluator.

## Repository setup and paths

The user has **already cloned and fixed Git version selection** for τ-bench; **do not clone it again**. Their intended layout is:

```text
<project-root>/
├── data/                         # Existing synthetic benchmark source data
├── llm_correctness/
│   ├── llm_judge.py              # EXISTING working judge; preserve synthetic behavior
│   └── ...
├── t-bench_data/
│   └── tau2-bench/               # Already cloned; intended version v1.0.1
├── <existing-synthetic-results>/ # Preserve all completed results
└── llm_tau2_results/             # New output directory (only when run)
```

The precise location of `llm_judge.py`, existing synthetic output directory, and project working directory must be **verified from the actual local filesystem**, rather than assumed from this diagram. The source provided by the user in chat is the authoritative baseline: `Pasted text(2).txt` (a complete version of `llm_judge.py`). If an on-disk judge differs, inspect the difference and preserve the actual running code. **Read actual files before modifying anything.**

Verify checkout and inspect the actual repository layout before writing the adapter:

```bash
git -C t-bench_data/tau2-bench describe --tags --exact-match
git -C t-bench_data/tau2-bench rev-parse HEAD
find t-bench_data/tau2-bench -maxdepth 5 -type f | head -100
```

The expected tag is **`v1.0.1`**; record the exact commit SHA with the evaluation outputs. The tag may be checked out in detached HEAD state; that is fine. If any paths or schemas differ from expectations, follow **the actual pinned v1.0.1 files**, not assumptions or the latest online documentation.

Full installation of τ-bench should not be necessary: inspect/read the benchmark files statically and use only the Python dependencies necessary for the existing judge and adapter.

## Existing judge: code audit and preservation contract

The supplied current `llm_judge.py` contains:

- `DIMENSIONS`: `task_consistency`, `expected_outcome_validity`, `policy_compliance`, `workflow_feasibility`.
- `PROMPT_VERSION = "1.0"` and `SYSTEM_PROMPT` beginning `You are auditing the correctness of SYNTHETIC benchmark TASK DATA, ...`.
- `DimensionJudgment` and `JudgeResult` Pydantic structured response models.
- `iter_tasks(data_dir, domain_filter)`: iterates synthetic domain directories, `test_cases.json` → `workflows` → `test_cases`.
- `static_python_context()`: AST extraction of matching synthetic test classes, reference tool calls, and signatures; does **not execute code**.
- `policy_context()`: reads synthetic `agent_definition.yaml`.
- `build_payload(folder, workflow, task)`: builds the synthetic payload with `domain`, `workflow`, `task`, `policy`, and `python_reference`.
- `judge_task(client, model, payload)`: calls `client.beta.chat.completions.parse(..., response_format=JudgeResult)`; **current version does not set `temperature`**. Preserve this unless explicitly directed otherwise.
- `make_record()`: assumes `payload['task']['test_case_id']` and `payload['task']['title']`; stores dimension judgments and equally weighted task score.
- `write_reports()`: writes `judge_details.json`, `task_scores.csv`, `domain_scores.csv`; `summary_row()` computes domain and task-weighted overall scores.
- `main()`: CLI with `--data-dir`, `--output-dir`, `--model` (defaults to `MODEL_NAME` env var), `--domain`, `--limit`, `--dry-run`, `--resume`. Uses `.env` via `load_dotenv()`; uses `OPENAI_API_KEY` for live calls.

**Nonnegotiable preservation:**

1. Keep the synthetic `iter_tasks`, `static_python_context`, `policy_context`, and `build_payload` behavior intact. Prefer a separate `tau_adapter.py` module and a narrow dispatch in the CLI.
2. Keep `DimensionJudgment`, `JudgeResult`, the four scores, and their calculation unchanged. Keep existing reporting files and CSV column formats compatible.
3. Keep the current synthetic `SYSTEM_PROMPT` and `PROMPT_VERSION = "1.0"` unchanged for synthetic runs, to avoid changing synthetic scores or resume behavior. The existing wording explicitly says `SYNTHETIC`, so create a **separate τ-bench prompt** with only the minimum dataset-neutral wording change (e.g., replace `SYNTHETIC benchmark TASK DATA` with `benchmark TASK DATA`). **Do not edit rubric text, evidence rules, weighting, or scoring scale.** Give the τ-bench prompt its own explicit version identifier in τ-bench records/resume metadata.
4. Keep `judge_task()` and its model options semantically identical; a small optional prompt parameter is acceptable if its default reproduces the original synthetic path exactly.
5. Do not overwrite, rewrite, migrate, or append to completed synthetic results. Keep all τ-bench results in a separate directory.
6. Preserve default CLI behavior: invoking without a dataset selector must still evaluate synthetic `data/` as before.

## Locked correctness methodology

Evaluate **each task**, independently, on:

| Dimension | Question |
|---|---|
| **T — Task consistency** | Are task instructions, conditions, scenario inputs, and milestones mutually consistent? |
| **O — Expected outcome validity** | Does the expected final outcome satisfy the task objective given the available evidence? |
| **P — Policy compliance** | Is the intended workflow consistent with supplied domain policies, checks, and escalations? |
| **F — Workflow feasibility** | Is at least one plausible workflow possible using the documented tools and initial state? |

Scores: **1.0 = supported/correct; 0.5 = uncertain/insufficient evidence; 0.0 = demonstrated contradiction/violation**. Each dimension must include **a concise explanation and specific evidence**. Do not invent requirements or capabilities; do not count missing evidence as confirmed error. Do not assume a reference sequence is the *only* acceptable sequence. Feasibility is plausibility, not proof of successful execution.

Task score: `L_i = (T_i + O_i + P_i + F_i) / 4`.
Overall score: arithmetic mean of the task scores (task-weighted, not an unweighted mean of domain means). Also report each domain's mean, number of uncertain and violated dimensions, and explanations/evidence in `judge_details.json`.

Do **not** introduce new weights, binary labels, hybrid deterministic/LLM scores, agent success metrics, or a different rubric. The goal is comparable **dataset quality/correctness**, not matching business domains. Differences in domain composition are an interpretation caveat, not a reason to redesign the scoring.

## Inspect τ-bench v1.0.1 before coding

Inspect the **actual files** for each domain (`airline`, `retail`, `telecom`), including where applicable:

- `tasks.json` — task IDs, instructions, and evaluation criteria;
- `policy.md` — applicable domain rules;
- domain `tools.py` and related tool definitions — actions, parameter types/descriptions, available capabilities;
- initial database/state files (`db.json`, `db.toml`, or other formats used by this pinned release);
- task split/index metadata if applicable;
- any extra relevant user-side tool definitions or task metadata.

The locations mentioned here are **search targets**, not guaranteed exact v1.0.1 paths. Inspect nested directories and actual schemas. Avoid importing or running benchmark domain modules just to inspect tool metadata: use static text or AST parsing when appropriate. Do not execute benchmark code, mutate its database, or start its environments.

Determine from the actual benchmark files which evaluation criteria specify a target database state, required user-facing communication, tool actions, or other assertions. Reference actions may illustrate **one successful path**, not the only valid one. For an outcome validity judgment, include the actual expected outcomes/checks, not merely the reference call sequence. Supply relevant initial-state values or task-specific extracts where needed; don't blindly insert huge entire databases into every LLM payload. Context selection should be sufficient, faithful, and repeatable. Missing policy, tool, or initial-state evidence should be surfaced rather than invented.

## Implementation steps

### 1. Add a separate `TauBenchAdapter`

Create a small adapter module (e.g., `llm_correctness/tau_adapter.py`) that:

1. Accepts a repository path, defaulting to **`t-bench_data/tau2-bench`** when running from the project root (allow an explicit CLI path to avoid fragile working-directory assumptions).
2. Iterates selected tasks in **airline, retail, and telecom** from the pinned benchmark; respects a domain filter, limit, stable ordering, and any relevant official split selection (determine the correct supported task set from v1.0.1; do not silently omit tasks).
3. Maps each task to the existing judge's essential payload: `domain`, task instructions and scenario, policy, available tool definitions, reference/evaluation criteria, and relevant initial state.
4. Maps the original task ID to `payload['task']['test_case_id']` and a meaningful title/label to `payload['task']['title']` for existing `make_record()` compatibility; preserve original IDs and any needed benchmark identifiers in extra metadata.
5. Reads benchmark code **statically**; never invokes benchmark tools or runs reference trajectories.
6. Produces a well-formed payload compatible with `judge_task()` using the existing four-dimension rubric. It may contain additional explicit keys (e.g., `evaluation_criteria`, `initial_state`) so long as the judge receives their meaning and source clearly.
7. Validates required fields, uniqueness of `(domain, task_id)`, readable source files, and task counts; fail explicitly on critical structural errors rather than passing empty placeholder evidence and producing misleading scores.

Keep the adapter simple. A common normalized task payload is sufficient; no generic multi-benchmark framework or deterministic evaluator is needed.

### 2. Add minimal CLI routing

Add a dataset selector such as `--dataset synthetic|tau2` (default `synthetic`) and a τ-bench root option such as `--tau2-dir t-bench_data/tau2-bench`. For `--dataset synthetic`, follow the *same codepath and defaults* as today. For `--dataset tau2`, use the new adapter and its benchmark-specific prompt wording, then call the shared `judge_task`, `make_record`, and `write_reports` functions.

Use separate output directories; for example `--output-dir llm_tau2_results` for τ-bench. Accept `--domain airline`, `--domain retail`, `--domain telecom`, `--limit`, `--dry-run`, `--resume`. If multiple domains are selected by default, evaluate all three.

Handle `--resume` using `(domain, task_id)` and matching model/prompt version, with **dataset separation** enforced via output folder and/or explicit metadata. Prevent accidental mixing of synthetic and τ-bench results. Resume only judgments generated under the same scoring/prompt configuration and pinned benchmark version; if necessary record SHA and reject a mismatched resumed run.

### 3. Keep structured scoring and reports unchanged

Re-use the Pydantic response, dimension calculation, and existing CSV/JSON writers. Preserve:

```text
llm_tau2_results/
├── judge_details.json  # task scores + all four explanations + evidence + model/prompt identifiers
├── task_scores.csv     # per-task scores and uncertainty counts
└── domain_scores.csv   # per-domain averages/counts + OVERALL task-weighted mean
```

Include reproducibility metadata such as benchmark tag/commit and task selection in a small additional metadata file or safe additive fields **only on the τ-bench side**; do not change or corrupt synthetic report compatibility.

### 4. Test before paid calls

- Run all existing unit tests without changing their expectations.
- Run the original synthetic `--dry-run` and confirm the same synthetic task count and payload shape (expected **64 tasks across seven domains**, if using the same data); compare representative synthetic payloads against baseline if feasible.
- Test the new adapter with small fixture files or actual v1.0.1 data to ensure domain/task IDs, instruction text, policy context, tool definitions, and expected outcomes are loaded correctly.
- Run a τ-bench `--dry-run` with **zero API calls** and inspect actual assembled payloads for **one task per domain**. Dry-run must not only count tasks: verify required evidence is actually present.
- Confirm no task ID collisions, no missing required source records, no accidental reading of the latest checkout instead of the pinned release, and no changes to the synthetic result directory.

### 5. Run a small live pilot

Evaluate **one task from each domain** (airline, retail, telecom), using the **same model** used for the synthetic dataset and the fixed τ-bench prompt variant. Verify that each dimension's 0/0.5/1 score is evidence-grounded, explanations mention actual fields/policy/tool criteria, and uncertainty is not automatically translated into incorrectness. Inspect the JSON and CSV outputs. Use small `--limit`/domain filters; do not run a full paid benchmark evaluation without a successful pilot.

### 6. Full evaluation and reporting

After pilot approval, evaluate the selected complete τ-bench v1.0.1 task set. Use `--resume` for interrupted runs, retaining partial outputs safely. Produce identical report schemas for easy downstream Jupyter notebook comparison:

- synthetic dataset vs τ-bench **overall task-weighted mean**;
- averages by domain and four scoring dimensions;
- uncertainty/violation counts;
- per-task explanations and cited supporting evidence.

Keep synthetic and τ-bench data separate. Do not claim τ-bench is a perfect reference; comparison measures judge-assessed task correctness, not ground-truth judge accuracy. Later perturbation validation is a **separate future phase** and is **not part of this implementation**.

## Example CLI (proposed, not yet implemented)

From the project root, after the implementation:

```bash
# Verify synthetic still works:
python llm_correctness/llm_judge.py --data-dir data --dry-run

# Verify τ-bench parsing (should make no API calls):
python llm_correctness/llm_judge.py \
  --dataset tau2 \
  --tau2-dir t-bench_data/tau2-bench \
  --dry-run

# Pilot in one domain; repeat for retail and telecom:
python llm_correctness/llm_judge.py \
  --dataset tau2 \
  --tau2-dir t-bench_data/tau2-bench \
  --domain airline \
  --limit 1 \
  --output-dir llm_tau2_pilot_results \
  --model <SAME_MODEL_AS_SYNTHETIC>

# Full τ-bench evaluation only after inspecting pilot outputs:
python llm_correctness/llm_judge.py \
  --dataset tau2 \
  --tau2-dir t-bench_data/tau2-bench \
  --output-dir llm_tau2_results \
  --model <SAME_MODEL_AS_SYNTHETIC> \
  --resume
```

These flags are the **implementation target** and are not present in the supplied current code. Adapt commands if the confirmed project layout differs. Do not hardcode API keys. `OPENAI_API_KEY` can be supplied through environment/`.env` as the current script does.

## Acceptance criteria / definition of done

- [ ] τ-bench is read from the existing `t-bench_data/tau2-bench` checkout at **v1.0.1** (commit recorded).
- [ ] Airline, retail, and telecom tasks load with valid unique IDs and expected total counts for the selected pinned task set.
- [ ] The adapter supplies task instructions, evaluation criteria, appropriate policy and tool context, and sufficient relevant initial-state context without executing benchmark code.
- [ ] All four scores, evidence, explanations, and equal-weight calculations remain unchanged.
- [ ] Synthetic evaluation still works with its prior CLI, default prompt, task count, output formats, and resume behavior.
- [ ] τ-bench evaluation uses its own output directory; no synthetic result data is modified.
- [ ] No-API dry run succeeds and representative payloads are manually checked for completeness.
- [ ] Live pilot succeeds for one task per domain and writes correct JSON and CSV output.
- [ ] The full task set can be evaluated and resumed using the same model used for synthetic judgments.
- [ ] Deliver a concise README with exact run commands, selected commit/task set, files changed, test results, and any known context/evidence limitations.

## Codex operating instructions

**First inspect the real project and checkout.** Then implement only the smallest necessary change set. In your response, explicitly identify files changed and which preservation tests passed. If a required source file or initial-state field is absent in v1.0.1, report the limitation and adapt to actual schema rather than inventing fields. Do not initiate costly live API calls unless explicitly authorized. Preserve the existing rubric and synthetic pipeline above all else.
