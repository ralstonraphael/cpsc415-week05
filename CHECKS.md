# Checks

All runs on October 25, 2026, Python 3.12.13, from the repository root.

## 1. The test loop: red, then green

Every component's tests were committed before its code. Each red run was taken with the code file absent, and the commit message records it.

| Step | Tests | Red (before the code) | Green (after) | Commits |
|---|---|---|---|---|
| 2. Checker | `tests/test_checker.py` | `1 error` (no module `checker`) | `15 passed` | `426c55a` → `8401620` |
| 3. Reader | `tests/test_reader.py` | `1 error` (no module `reader`) | `43 passed` | `91d5b87` → `fb61256` |
| 4. Command line | `tests/test_cli.py` | `1 error` (no module `receipts`) | `5 passed` | `c602476` → `43042eb` |
| 5. Merchant compare | `tests/test_merchant.py` | `1 error` (no module `merchant`) | `6 passed` | `89b8bb3` → `b580285` |

All tests that need no key: `python -m pytest -m "not eval"` → **69 passed, 25 deselected**.

**Did the tests prove anything?** Two deliberate breaks:
- **Checker:** changing `round(x * 100)` to `int(x * 100)` (truncating instead of rounding) turned 2 tests red: `test_consistent_discount_receipt` (1.15 × 100 truncates to 114) and `test_amounts_are_rounded_not_truncated` (0.29 + 0.71 comes to 99 cents). The first time we tried this, only one test caught it. The 0.29 test was added so a second, independent receipt guards the rule.
- **Merchant:** the strict compare is kept beside the word-set one, so the eval shows what each would say.

## 2. The eval on both models

`python -m pytest -m eval -v`, then `python eval.py` for the table. One model call per image, cached for the session: 5 calls per model, not 25.

**`xiaomi/mimo-v2.6-flash`** (the default; reasoning off): pytest `25 passed`

| Receipt | Total | Items | Merchant (word set / strict) | Date | Checker | Tokens in / out |
|---|---|---|---|---|---|---|
| receipt-01.png | pass | pass | pass / pass | pass | clean | 562 / 138 |
| receipt-02.png | pass | pass | pass / pass | pass | clean | 562 / 274 |
| receipt-03.png | pass | pass | pass / pass | pass | clean | 562 / 139 |
| receipt-04.png | pass | pass | pass / pass | pass | clean | 628 / 174 |
| receipt-05.png | pass | pass | pass / FAIL | pass | clean | 562 / 156 |

25 of 25 checks passed. 5 model calls, 2,876 tokens in, 881 out.

**`minimax/minimax-m3`** (only `CHAT_MODEL` changed; reasoning on): pytest `25 passed`

| Receipt | Total | Items | Merchant (word set / strict) | Date | Checker | Tokens in / out |
|---|---|---|---|---|---|---|
| receipt-01.png | pass | pass | pass / pass | pass | clean | 877 / 219 |
| receipt-02.png | pass | pass | pass / pass | pass | clean | 877 / 408 |
| receipt-03.png | pass | pass | pass / pass | pass | clean | 877 / 294 |
| receipt-04.png | pass | pass | pass / pass | pass | clean | 925 / 322 |
| receipt-05.png | pass | pass | pass / FAIL | pass | clean | 877 / 256 |

25 of 25 checks passed. 5 model calls, 4,433 tokens in, 1,499 out.

**What differed:** nothing in accuracy on these five. minimax used about 1.5× the input tokens and 1.7× the output tokens; part of its output is hidden reasoning (about 90–100 tokens a receipt in the probe). At October 25 prices that is about $0.0006 a receipt on minimax against $0.00013 on mimo, which is why the spec defaults to mimo.

### Failures, and whether the model or the spec was at fault
- **Receipt 5, strict merchant compare: spec ambiguity, not a misread.** The receipt prints "Bake Sale - CS Club"; the answer key says "CS Club Bake Sale". Both models read the receipt correctly. The spec decided before any eval run (behavior 13) that names match on the same set of words. The key was not edited.
- **Receipt 1, merchant, in the pre-spec probe: spec ambiguity, fixed in the instruction.** Before the spec existed, minimax answered "Mather Dining Hall, Trinity College, Hartford CT", adding the address line. The instruction now says "the business name only, as printed, without the address", and minimax passes. The word-set compare deliberately does *not* accept extra words (`test_extra_words_do_not_match`).
- **The discount's sign** on receipt 3 ("Student discount -1.15") was read as a positive 1.15 by both models, as the instruction asks. The checker would report a negative discount if one came back.

## 3. The linter

`uvx ruff check .` found 2:
- `reader.py:219` UP041: `socket.timeout` is an alias of `TimeoutError`. Fixed: catch `TimeoutError` only, and `import socket` removed. 69 no-key tests still pass.
- `.claude/hooks/guard.py:28` PIE810: call `startswith` once with a tuple. **Not changed**, because this is the course's guard hook, copied as given. Style only, no behavior impact.

After the fix, ruff reports `All checks passed!` on all our files.

## 4. Breaking the loop on purpose (lab step 4)

*To be recorded.*

## 5. My own receipts

*To be recorded.*
