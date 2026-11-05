# Validation progress report

Date: November 4, 2026

## Current assessment

The deterministic validation framework is implemented, with saved passing corruption experiments for all three τ² domains. It detects the seven constructed error types with the expected check-level score changes. This supports those specific detection capabilities; it does not establish complete semantic correctness or a general false-positive rate on original benchmark tasks.

This report reviews the current source, tests, and saved artifacts under `output/`. Saved experiment results were inspected, not regenerated for this report. They describe the inputs and implementation recorded in those artifacts and should be regenerated for a release snapshot.

## Completed work

- **Operational evaluation:** schema, tool signatures, entity references, and output consistency checks; task scores average applicable checks and dataset scores average tasks. Unavailable/blocked checks and full coverage are reported separately.
- **τ² integration:** retail, airline, and telecom task loading; isolated database replay; initialization handling; domain-specific ownership/reference checks; assistant/user tool handling for telecom; pinned runtime and source hashes.
- **Controlled validation:** seven campaigns—malformed action, unknown tool, wrong type, missing argument, unexpected argument, missing entity, and broken precondition. Seeded nested subsets test several corruption rates. Assertions cover score decreases, intended-check detection, complete expected check vectors, and expected versus observed aggregate scores.
- **Clean controls:** 20 constructed tasks per τ² domain, with executable outcome expectations. These support controlled false-positive testing and are distinct from human-reviewed original benchmark labels.
- **Synthetic reader:** static fixture inspection without importing LLM-initializing code; readers for all seven repository domains; static checks and corruption experiments. Static results do not provide real database/replay evidence.
- **Recorded runs:** separate half-duplex replay workflow with embedded-task preservation, drift checks, output pairing/comparison, and separate outcome evidence.
- **Reporting:** Markdown, JSON evidence, CSV, manifests, terminal summaries, exclusions, coverage, and error diagnostics. Baseline-only, failed, inconclusive, and passing validation states are distinguished.
- **Automated tests:** scoring, mutation selection, invalid verdicts, false positives, reporting, static readers, real tools, state isolation, initialization, domain parity, and recorded-run behavior.

## Available results

### Original τ² tasks

| Domain | Tasks | Operational score | Passing applicable checks | Fully evaluated | Corruption validation | Outcome results |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Retail | 114 | 95.7% | 99/114 | 97/114 | PASS | 114 not evaluated |
| Airline | 50 | 100% | 50/50 | 41/50 | PASS | 50 not evaluated |
| Telecom | 114 | 100% | 114/114 | 71/114 | PASS | 114 passed |

Sources: [retail](../output/tau2-retail-validation/report.md), [airline](../output/tau2-airline-validation/report.md), [telecom](../output/tau2-telecom-validation/report.md).

All seven campaigns were exercised in each domain. Target-check detection was 100% for every nonzero-corruption row. Original-task false-positive rates are unavailable because these runs have no independently labeled clean original tasks. Telecom's outcome passes reflect the executable expectations available to this workflow, rather than proof of every possible conversational or policy requirement.

Retail has 15 tasks with at least one operational failure: five reference-check failures and ten output-consistency failures. Findings include missing products/orders and user lookups returning “User not found.” These need review against the supplied snapshot before assigning root causes to task data, snapshot mismatch, or evaluator behavior.

### Constructed controls and other workflows

| Run | Evidence | Interpretation |
| --- | --- | --- |
| Retail, airline, telecom controls | Each: 20/20 passing, fully evaluated, 20 outcome passes, 0/20 baseline false positives; all seven campaigns PASS | Positive evidence on constructed cases; limited generalization to original tasks |
| Synthetic banking | 6 tasks; 62.5% score; 0/6 passing; validation INCONCLUSIVE | Three signature failures, six reference failures; `inconsistent_case_id` campaign unexercised |
| Recorded-run sample | 2/2 passing applicable checks; 1/2 fully evaluated; 2 outcome passes | Small workflow demonstration; corruption validation not run |
| Original demo | 20 tasks; 100% baseline; validation PASS; zero baseline false positives | Harness sanity check using controlled demo fixtures |

Sources: [retail controls](../output/tau2-retail-controls/report.md), [airline controls](../output/tau2-airline-controls/report.md), [telecom controls](../output/tau2-telecom-controls/report.md), [synthetic banking](../output/synthetic-banking/report.md), [recorded sample](../output/tau2-recorded-sample/report.md), [demo JSON](../output/correctness-validation/report.json).

Synthetic banking reports no tasks fully evaluated in the stronger coverage sense, even though static values exist for all four categories. Its score must retain the static-only qualification.

## Remaining validation work

These are recommended next steps based on observed gaps, rather than claims that every item is an existing project requirement.

| Priority | Work | Completion evidence |
| --- | --- | --- |
| High | Review the 15 retail failures against task definitions, initialization, and the recorded database snapshot | Per-task adjudication with root cause and regression test or documented data defect |
| High | Add independently reviewed labels to representative original tasks, including valid edge cases | Reviewed labels with provenance; report false positives and sample denominators separately from constructed controls |
| High | Resolve synthetic banking inconsistencies and its unexercised campaign | Reviewed fixture/evaluator fixes where justified; campaign exercised or explicitly documented as inapplicable; regenerated report |
| High | Run and save static validation for the other six synthetic domains | Per-domain baseline, coverage, exclusions, and corruption results; loading tests alone are insufficient |
| High | Add independent executable outcome expectations for retail and airline where feasible | Explicit outcome passes/failures and uncovered requirements; no targets derived from the same reference replay as proof of reference success |
| Medium | Audit unavailable checks: 17 retail, 9 airline, and 43 telecom tasks lack full four-check coverage | Classify each case as legitimately inapplicable, blocked, or missing support; improve coverage where appropriate |
| Medium | Expand recorded-run evaluation beyond the two-run sample | Representative successful and failing recordings, supported reward components, output mismatches, and documented snapshot limitations |
| Medium | Broaden robustness experiments | Additional mutation variants, combinations/order edge cases, reviewed clean cases, and multiple seeds; retain per-task evidence |
| Medium | Make validation repeatable in CI | Lightweight tests plus pinned real-tool integration job; persist test results and validation artifacts for a known source revision |
| Optional extension | Evaluate semantic instruction following, conversational confirmation, and policy compliance | Independent reviewed rubric/assertions or a separately validated judge; the external LLM-mode scoring contract alone is not a judge implementation |

## Verification performed for this report

- Default test discovery: **43 tests discovered; 20 passed, 23 skipped** because the benchmark-root environment variable was unset.
- Full integration suite with `TAU2_BENCHMARK_ROOT` set to the local benchmark checkout: **43/43 passed, no skips** (23.3 seconds).

## Interpretation rules

A validation PASS means the declared corruption experiments behaved as expected. A 100% operational score can include unavailable checks. Constructed-control false positives do not estimate a general population rate. Outcome evidence is separate from the operational score. `NOT RUN` in baseline-only or recorded-run reports means corruption validation was not requested.
