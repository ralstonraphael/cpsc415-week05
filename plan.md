# Plan

Implements [`spec.md`](spec.md) (approved October 25, 2026). Python 3.12, standard library for the program, pytest for the tests.

## Files to create or change
| File | Purpose |
|---|---|
| `models.py` | `Item`, `Receipt`, `ReadFailure` dataclasses shared by the reader, the checker and the tests. No logic. |
| `checker.py` | `check(receipt) -> list[str]`: the arithmetic in whole cents (spec behaviors 5–8). |
| `reader.py` | `build_request(image_path, model) -> dict`, `parse_reply(text, finish_reason) -> Receipt \| ReadFailure`, `read_receipt(image_path) -> Receipt \| ReadFailure`, and the per-model reasoning table (behaviors 1–4, 9, 10). |
| `receipts.py` | Command line: `python receipts.py photo.png` (behavior 11 and the exit codes). |
| `eval.py` | Prints the per-receipt comparison table with tokens, for `CHECKS.md`. |
| `merchant.py` | `same_merchant(a, b)`: the word-set compare from behavior 13, used only by the eval. |
| `tests/test_checker.py` | No key: hand-written receipts, consistent and not. |
| `tests/test_reader.py` | No key: reply parsing (bare, fenced, prose, not JSON, wrong shape, empty with `length`), the request body, the reasoning table. |
| `tests/test_cli.py` | No key: missing key exits 2 with no request; a failed read exits 1. |
| `tests/test_merchant.py` | No key: the word-set compare. |
| `tests/test_eval.py` | Eval, marked `eval`, skipped without a key: one model call per image, cached for the session; `test_total`, `test_item_count`, `test_merchant`, `test_date`, `test_checker_clean`, each per image. |
| `pytest.ini` | Registers the `eval` marker; `testpaths = tests`. |
| `requirements-dev.txt` | `pytest` (the only dependency, listed in the spec). |
| `CHECKS.md`, `README.md` | Results and how to run, after the eval. |

## Order of work
1. **Shared types** (`models.py`). Everything else imports them, so they come first. No tests: there is no behavior in them.
2. **Checker, tests first.** Write `tests/test_checker.py`, run it red, write `checker.py`, run it green.
3. **Reader parsing, tests first.** Write `tests/test_reader.py`, run it red, write `reader.py`, run it green. Steps 2 and 3 do not touch each other's files, so they can run in parallel.
4. **Command line, tests first.** `tests/test_cli.py`, then `receipts.py`.
5. **Merchant compare, tests first.** `tests/test_merchant.py`, then `merchant.py`.
6. **Eval.** `tests/test_eval.py` and `eval.py`. Run on `xiaomi/mimo-v2.6-flash`, then change only `CHAT_MODEL` to `minimax/minimax-m3` and run again. Record both in `CHECKS.md` with tokens.
7. **Lint.** `uvx ruff check .`, fix, record the findings.
8. **Break the loop on purpose** (lab step 4): change receipt-01's total in the key by hand to 13.96, run the eval, ask the agent to "make it pass", record what it does and the hook's message, restore the key with `git checkout -- images/expected.json` by hand.
9. **Own receipts.** Two photos in `my-receipts/` with a hand-written `expected.json`, eval on both models, README.

## Risks
- **R1. A test passes for the wrong reason.** For example, a checker test that only ever sees consistent receipts would pass even with no checking at all. Mitigation: every rule gets a failing receipt as well as a passing one. On step 2 we break the checker on purpose (drop the cents rounding) and watch a test go red.
- **R2. Float money.** `0.89 * 3` is `2.6700000000000004`. Mitigation: every amount becomes `round(x * 100)` before comparing; behavior 6 has a float-noise test and a one-cent test.
- **R3. The eval calls the model once per test**, which is 25 calls instead of 5, five times the cost and slow. Mitigation: a session-scoped fixture reads each image once and every test looks up the cached result. Proof: the eval prints 5 calls in its token summary.
- **R4. mimo spends its output thinking** (empty content, `finish_reason: length`). Mitigation: the reasoning table sends `enabled: false` for mimo only; behavior 4 turns an empty `length` reply into a readable failed read instead of a parse error.
- **R5. The model is right and the key is wrong.** Receipt 5 prints "Bake Sale - CS Club"; the key says "CS Club Bake Sale". Mitigation: behavior 13's word-set compare, decided in the spec before any result was known. Any other disagreement fails the test and is explained in `CHECKS.md`. Nobody edits `images/`; the hook enforces it.
- **R6. The agent edits the answer key to make a test pass.** Mitigation: `.claude/hooks/guard.py` blocks edits and writes to `images/` and `expected.json`; step 8 tests it for real.
- **R7. A key in the repo.** Mitigation: the key is only read from the environment, `.env` is ignored, and `git grep sk-or` is empty before the push.

## Proof
**Tests that need no key** (`python -m pytest -m "not eval"`), run on every step. Each proves a behavior without the network:

| Step | Command | Proves |
|---|---|---|
| 2 | `pytest tests/test_checker.py -v` | The arithmetic rules on hand-written receipts: items vs subtotal, subtotal − discount + tax vs total, one cent reported, float noise not, negatives and empty lists reported, a consistent receipt clean (behaviors 5–8). Red before `checker.py` exists, green after. |
| 3 | `pytest tests/test_reader.py -v` | Parsing never crashes: bare, fenced and prose JSON give the same receipt; non-JSON, wrong shape and empty `length` replies are failed reads with a reason; `null` dates stay `None`; the request body carries the image part and the reasoning setting per model (behaviors 1–4, 9, 10). |
| 4 | `pytest tests/test_cli.py -v` | No key exits 2 with no request; a failed read exits 1 (behavior 11). |
| 5 | `pytest tests/test_merchant.py -v` | The word-set compare (behavior 13). |

On their own, these prove our code handles every reply shape and every arithmetic case. They prove nothing about whether a model can read a receipt. That is the eval's job.

**The eval, which needs a key** (`python -m pytest -m eval -v`, then `python eval.py`), step 6. It compares each image in `images/` with `images/expected.json`: total to the cent, number of items, merchant, date, and a clean checker (behavior 12), once per model. Output that means it worked: 25 test results per model (5 fields × 5 receipts), 5 model calls per model, and a table in `CHECKS.md` with tokens in and out per receipt. A red test here is a finding to explain (model misread or spec ambiguity), not a bug to hide.

## Questions asked before approval
- **"Which tests run without the key, and what do they prove on their own?"** Everything except `tests/test_eval.py`. They prove the parsing and the arithmetic on inputs we wrote by hand, including bad ones. They cannot prove the model reads receipts correctly.
- **"What does the eval compare against, and what if the model is right and `expected.json` is wrong?"** It compares against `images/expected.json`. If the model is right and the key is wrong, the test stays red and `CHECKS.md` says so with the evidence. We never edit the key or special-case the code. Receipt 5's merchant word order is the one case decided in advance, in the spec, as a rule for all names. *Correction from this answer:* step 6 now records the result of a strict string compare next to the word-set result, so the spec decision is visible rather than silent.
- **"What could break in step 3, and how would I notice?"** A model reply with JSON inside prose and a stray `}` later in the text could make the extraction take too much. We'd notice because the prose test fails. The reader takes the first balanced `{...}` that parses, and the tests include a reply with text after the object.

## Subagents and parallel work
Steps 2 and 3 run in parallel as two Sonnet subagents, one for the checker and one for the reader. Each owns only its own files and writes the tests first. Each runs them red, writes the code, runs them green, and returns both outputs. Neither one commits. The main session reviews each diff and commits the tests and then the code, in that order, so the history shows tests before code. It also replays the red run at commit time. Everything else stays in the main session, because each step needs the one before it.

**Approved by:** Ralston Raphael, October 25, 2026
