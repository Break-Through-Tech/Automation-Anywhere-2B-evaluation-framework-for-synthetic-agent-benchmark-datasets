# Correctness validation framework

`correctness_checker.py` tests an evaluator by introducing known corruptions
and checking per-category detection and expected changes in dataset score.
The built-in evaluator is a toy demonstration, not a real dataset evaluator.

Run from the repository root:

```bash
.venv/bin/python -m validation.correctness_checker --demo
.venv/bin/python -m unittest validation.test_correctness_checker
```

The framework supports four deterministic categories with binary scores and four
LLM categories with 0/0.5/1 scores. Inapplicable checks can be `null`. Task scores
average applicable checks; dataset scores average task scores. No LLM calls are
made by the framework itself.

To connect an external evaluator, use `--input manifest.json --evaluator
module:function`, with `--mode deterministic` or `--mode llm`. The evaluator must
return a `checks` dictionary. Run `--help` for its contract and mutation format.

The dataset and LLM evaluator implementations, their tests, and their detailed
documentation are parked outside this repository in the sibling folder
`../correctness-evaluators-stash-2026-10-28/`. That folder also includes copies of
the primary checker and its tests to preserve the evaluators' imports.
