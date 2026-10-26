# Week 5: Receipts to data, with tests

CPSC 415, Ralston Raphael. A command-line program that reads a photo of a receipt with a vision model and returns JSON. Plain code then checks that the items add up to the subtotal and that subtotal − discount + tax is the total. The model reads; our code decides whether the numbers add up.

The chain: [`intent/receipts.md`](intent/receipts.md) → [`spec.md`](spec.md) → [`plan.md`](plan.md) → tests and code → [`CHECKS.md`](CHECKS.md).

## Run it

Python 3.12. The program uses only the standard library; the tests need pytest.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
export OPENROUTER_API_KEY=<your key>          # never committed
.venv/bin/python receipts.py images/receipt-01.png
```

| Variable | Meaning | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | needed for the program and the eval | none |
| `CHAT_MODEL` | which vision model reads the receipt | `xiaomi/mimo-v2.6-flash` |
| `CHAT_REASONING` | `on` or `off`, overrides the per-model table | mimo off, others on |
| `CHAT_BASE_URL` | the chat endpoint | `https://openrouter.ai/api/v1` |
| `RECEIPT_DIR` | the folder the eval reads, with its `expected.json` | `images` |

## Tests

```bash
.venv/bin/python -m pytest -m "not eval"   # 69 tests, no key, no network
.venv/bin/python -m pytest -m eval -v      # the eval: needs the key, skipped without it
.venv/bin/python eval.py                   # the eval as a table with tokens
```

- **No key needed:** the checker, the reply parsing, the request body and the command line, all on hand-written inputs. They prove the code handles every reply shape and every arithmetic case. They say nothing about whether a model can read a receipt.
- **Key needed (the eval):** reads each image once and compares it with `images/expected.json`: the total, the number of items, the merchant, the date, and a clean checker.

## Two models

| Model | Checks passed | Tokens in / out (5 receipts) | About per receipt |
|---|---|---|---|
| `xiaomi/mimo-v2.6-flash` (default, reasoning off) | 25 / 25 | 2,876 / 881 | $0.00013 |
| `minimax/minimax-m3` (reasoning on) | 25 / 25 | 4,433 / 1,499 | $0.0006 |

Both models read every total, item count, merchant and date correctly, and every receipt's arithmetic held. They differed in cost: minimax spent about 1.5× the input and 1.7× the output tokens, partly on hidden reasoning, so mimo is the default. Full per-receipt tables are in [`CHECKS.md`](CHECKS.md).

## Step 4: when a test disagreed with the answer key

*To be filled in after the run.*

## My own receipts

*To be filled in after the run.*

## One line I can explain

```python
expected = subtotal - cents(receipt.discount) + cents(receipt.tax)
```

From `checker.py`. Every amount has already been turned into whole cents with `round(x * 100)`, so this is integer arithmetic and 0.1 + 0.2 cannot come out as 0.30000000000000004. The discount is stored as a positive number, so it is subtracted. If `expected` differs from the printed total, even by one cent, the checker reports both amounts and the difference instead of trusting the model.
