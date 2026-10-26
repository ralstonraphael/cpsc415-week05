# Project conventions

<!-- The agent reads this at the start of every session. Keep it short and current.
     Graded: does it reflect how the team actually works? -->

## What this repository is
The Week 5 lab: a command-line receipt reader. A vision model reads a receipt photo into JSON, and plain code checks the arithmetic. See [`spec.md`](spec.md).

## Commands
```
# build   python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
# test    .venv/bin/python -m pytest -m "not eval"   (no key)   |   -m eval   (needs OPENROUTER_API_KEY)
# run     .venv/bin/python receipts.py images/receipt-01.png
# lint    uvx ruff check .
```

## Conventions
- Python 3.12, standard library only in the program; pytest for tests.
- Tests in `tests/test_<module>.py`, written and committed before the code they test.
- No branches or pull requests this week (see Working rules).

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- Write or update `intent/` and `spec.md` before code. Get `plan.md` approved before implementing.
- One feature per branch and pull request. Never push to `main` directly.
- Never commit `.env` or `.claude/settings.local.json`.
- This is the Week 5 introductory lab. Stages assigned: intent, spec, plan,
  and tests. No branches or pull requests yet. Commit to main.
- Libraries and build tools are allowed. Name each dependency in spec.md
  under Dependencies, with the reason, before installing it; a hook blocks
  installs that spec.md does not list.
- images/ and images/expected.json are the answer key. Never edit them. If
  a test disagrees with the key, say so and stop.
- Tests live in tests/ (Python) or src/test (Java). Tests that call a model
  are marked and are skipped when no API key is set.

## Common mistakes
Things the agent got wrong before and must not repeat. Add to this list as they happen.
