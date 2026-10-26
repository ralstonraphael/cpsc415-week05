# Spec: Receipt reader with an arithmetic check

## Intent
Implements [`intent/receipts.md`](intent/receipts.md) (approved October 25, 2026).

One run: `python receipts.py photo.png` → the **reader** sends the image to a vision model and turns the reply into a receipt (or a failed read) → the **checker** does the arithmetic in plain code → the program prints the receipt as JSON and the list of problems. The model reads; only our code decides whether the numbers add up.

## Components

### Reader
- **What it does:** Encodes the image as a base64 data URL, sends it with one fixed instruction to the chat endpoint, takes the JSON object out of the reply, and validates its shape. It returns a `Receipt` or a `ReadFailure` with the reason. It never raises on a bad reply and never asks the model to check its own arithmetic.
- **Language:** Python 3.12, standard library for the program (`urllib.request`, `json`, `base64`). **Why:** the Week 2 and 3 programs are Python on the same endpoint, and the standard library is enough for one HTTP POST. Alternative: Java with `java.net.http` and a JSON library jar. That works too, but it adds a build for a single request and a JSON parse.
- **Model:** default `xiaomi/mimo-v2.6-flash`, compared with `minimax/minimax-m3`. Both are the class vision models, chosen with `CHAT_MODEL`. **Why:** measured on all five course receipts on October 25:
  - Both got every total, date and item count right, and every receipt's arithmetic held.
  - minimax put the address line into the merchant name on receipt 1 ("Mather Dining Hall, Trinity College, Hartford CT"); mimo did not.
  - mimo always wraps its JSON in a ```` ```json ```` fence; minimax returns bare JSON.
  - mimo costs about $0.00013 per receipt against minimax's $0.00057, about 4× cheaper.
  - mimo is the default: equal accuracy on the five receipts, a cleaner merchant name, and a quarter of the cost. *(Correction at approval: the first draft defaulted to minimax because it was the model announced in class; Ralston changed it on the probe's numbers.)* The eval in `CHECKS.md` re-checks the choice on both models.
- **Reasoning setting (per model):** sent as `"reasoning": {"enabled": false}` only for models in a small table in the code, which holds just `xiaomi/mimo-v2.6-flash`. The course found mimo can spend its whole output budget thinking, and that minimax with reasoning off stops reading the faded date. `CHAT_REASONING=on|off` overrides the table for one run.
- **Instruction to the model (fixed):** read the receipt and reply with one JSON object `{merchant, date, items: [{name, quantity, unit_price}], subtotal, discount, tax, total}`.
  - `merchant` is the business name only, as printed, without the address.
  - `date` is `YYYY-MM-DD`, or `null` when the year is not printed; a two-digit year means 20YY.
  - A line like `2 x Blue book @ 1.25` is one item with quantity 2 and unit price 1.25.
  - `discount` is a positive amount that is subtracted. `discount` and `tax` are 0 when absent; `subtotal` is the items total when no subtotal line is printed.
- **Interfaces:** `read_receipt(image_path) -> Receipt | ReadFailure`. `Receipt` holds the fields above plus `usage` (prompt and completion tokens) and the model name. Environment: `OPENROUTER_API_KEY` (required), `CHAT_MODEL` (default above), `CHAT_BASE_URL` (default `https://openrouter.ai/api/v1`), `CHAT_REASONING` (optional).
- **Dependencies:** none beyond the standard library.

### Checker
- **What it does:** Takes a `Receipt` and returns a list of problems, each a plain sentence with the amounts. It converts every amount to whole cents first (`round(x * 100)`), so 0.1 + 0.2 never fails a check. It never changes the receipt.
- **Language:** Python. **Why:** pure logic with no I/O, tested without a key; same language as the reader.
- **Model:** none, on purpose.
- **Interfaces:** `check(receipt) -> list[str]` (empty means no problems).
- **Dependencies:** none.

### Command line and eval (thin, around the two components)
- `python receipts.py photo.png` prints the receipt as indented JSON, then `Problems:` with one line each, or `No problems.` For a failed read it prints `Failed read: <reason>` and exits with status 1. A missing key prints how to set it and exits with status 2, with no network call.
- The eval is a pytest file marked `eval` that reads every image in `RECEIPT_DIR` (default `images/`) **once per image** and compares each with `RECEIPT_DIR/expected.json`. Tests are named per field and image, for example `test_total[receipt-01.png]`. `python eval.py` prints the same comparison as a table with tokens, for `CHECKS.md`.

## Behavior
*(no key)* tests use hand-written inputs and run anywhere; *(eval)* tests call the model and are skipped when `OPENROUTER_API_KEY` is unset.

1. A reply that is bare JSON, fenced JSON, or JSON inside prose parses to the same receipt. *(no key)*
2. **A reply that is not JSON is a failed read, not a crash:** `read_receipt` returns a `ReadFailure` with the reason, and the command line prints it and exits 1. *(no key)*
3. A reply with JSON of the wrong shape is a failed read naming the field. Examples: a missing `total`, `items` not a list, an item without `unit_price`, an amount that is not a number, a date that is not `YYYY-MM-DD` or null. *(no key)*
4. An empty reply with `finish_reason: "length"` is a failed read that says the model used its whole output budget. *(no key)*
5. **A receipt whose numbers do not add up is reported with the discrepancy:**
   - Items that do not sum to the subtotal produce `items add up to $X but the subtotal is $Y (off by $Z)`.
   - A subtotal, discount and tax that do not produce the total produce `subtotal - discount + tax is $X but the total is $Y (off by $Z)`.
   - Both can appear at once. *(no key)*
6. A difference of exactly one cent is reported; amounts that differ only by float noise, like 0.1 + 0.2 against 0.3, are not. *(no key)*
7. A negative discount, tax, quantity or unit price, and an empty item list, are each reported as a problem. The checker never flips a sign or fills in a value. *(no key)*
8. A consistent receipt produces no problems. *(no key)*
9. **The date is null when the year is not printed:** the reader keeps a `null` date as `None`, and the instruction tells the model to do this. Receipt 5 has no year, and the eval expects `None`. *(no key for the parsing; eval for the model)*
10. The request body has the image as an `image_url` part with a `data:image/png;base64,` URL, the fixed instruction, the model from `CHAT_MODEL`, and `reasoning.enabled: false` only for the models in the table, or as `CHAT_REASONING` says. *(no key)*
11. With no key, the command line exits 2 with a message and makes no network call. *(no key)*
12. For each image in `RECEIPT_DIR`, against its `expected.json`, the eval checks: the total to the cent, the number of items, the merchant, the date, and that the checker reports no problems. The model is called once per image, not once per test. *(eval)*
13. The merchant comparison in the eval ignores case, punctuation and word order. Two names match when they have the same set of words. This is a spec decision for the eval, not an edit to the key: receipt 5 prints "Bake Sale - CS Club" and the key says "CS Club Bake Sale". `CHECKS.md` records what a strict string compare would have said. *(no key for the compare function; eval for the model)*

## Failure handling
| Case | What happens |
|---|---|
| No `OPENROUTER_API_KEY` | Command line exits 2 with how to set it; eval tests are skipped; no request is sent. |
| Image file missing or not readable | Command line prints the path and exits 1. |
| HTTP error from the endpoint (400, 401, 402, 429, 5xx) | Failed read with the status and the provider's message. No automatic retry: the user reruns. |
| Timeout (60 s) | Failed read: "the model did not answer within 60 s". |
| Reply not JSON, wrong shape, or empty | Failed read with the reason (behaviors 2–4). |
| Numbers that do not add up | Not an error: the receipt prints, and the checker lists each problem with amounts (behavior 5). |
| Answer key disagrees with what the model read | The eval test fails and the failure is explained in `CHECKS.md` as a model misread or a spec ambiguity. `images/` and `expected.json` are never edited. |

## Dependencies
| Package | Used for | Why |
|---|---|---|
| pytest | the test runner, `-m eval` marker, `skipif` without a key | The course's runner for Week 5. Without it we would hand-roll a runner and skip logic. Test-only, not imported by the program. |
| ruff | the linter, run as `uvx ruff check .` | The lab asks for a linter pass. Run through `uvx`, so nothing is installed in the project. |

The program itself uses only the standard library.

## Cost estimate
Measured on October 25: about 790 tokens in and 250–380 out per receipt on minimax (about 90–100 of them hidden reasoning), about 500 in and 170–270 out on mimo.
- **Per receipt:** about $0.0006 on minimax, $0.00013 on mimo.
- **One full eval** (five receipts, both models): about $0.004.
- **The whole lab,** including a dozen eval runs and the step-4 exercise: under $0.10.

## Out of scope
Carried over from the intent:
- Fixing receipts or guessing missing numbers.
- Storing results or paying anyone.
- A web page, folders on the command line, currencies other than dollars.

Ruled out by this design:
- Asking the model whether its numbers add up.
- Automatic retries.
- Using `response_format` JSON mode as the only defense. It may be tried as an extra, but the parser must handle prose and fences either way.

**Approved by:** Ralston Raphael, October 25, 2026
