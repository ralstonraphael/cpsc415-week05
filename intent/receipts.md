# Intent: Receipt reader with an arithmetic check

## Goal
A command-line program that takes one photo of a receipt, asks a vision model to read it into JSON (merchant, date, items with quantity and unit price, subtotal, discount, tax, total), and then checks in plain code that the items add up to the subtotal and that subtotal, discount and tax produce the total. It reports the problems it finds; it does not fix them. An eval runs the five course receipts through it so two models can be compared on the same images.

## Who it is for
A student-club treasurer who reimburses members from photos of their receipts. Today they read each receipt and add it up by hand before paying. The program does the typing, and the check tells them which receipts to look at twice, because a vision model returns plausible numbers, not guaranteed ones.

## Constraints
- Run as `python receipts.py photo.png`: prints the JSON and then the list of problems (or "no problems").
- The model reads; our code checks. The model is never asked whether its own numbers add up.
- Exact to the cent: amounts are compared in whole cents, and any difference, even $0.01, is reported with the amount.
- A discount is written as a positive amount that is subtracted (total = subtotal - discount + tax). A negative discount is reported as a problem, not silently flipped.
- The two class vision models on OpenRouter, with the key from the environment and the model from `CHAT_MODEL`. Changing models changes only that variable.
- No API key in the repository, a commit, or any output. A full eval (five receipts, two models) should cost a few cents at most.
- Due Monday, October 26, 2026, 1:30 PM.

## Not in scope
- Fixing a bad receipt, guessing missing numbers, or storing results.
- Paying anyone, or anything about the club's money beyond reading one receipt.
- A web page, folders of receipts on the command line, or currencies other than dollars.
- Card numbers and names: the photos are cropped before they reach the program.

## Success looks like
1. On a receipt whose numbers add up, the program prints the JSON and "no problems".
2. On a receipt whose total is wrong (for example, a total one dollar too high), it reports the mismatch and the size of the difference in dollars and cents.
3. A receipt that does not print the year comes back with `date: null`, not a guessed year.
4. If the model's reply is not JSON, or is JSON inside prose or code fences, the program either parses the object out or reports a failed read. It never crashes.
5. The eval reports, per receipt and per model, whether the total, item count, merchant and date match `images/expected.json` and whether the checker found problems, with tokens used.

## Open questions
Settled in the interview (October 25):
- For: a club treasurer checking reimbursement receipts.
- Interface: command line, one image per run.
- Tolerance: exact to the cent.
- Discount sign: positive, subtracted.

Left for the spec, from a first look at how both models read the five receipts:
- What counts as the merchant name. One model added the address line to it. Receipt 5 prints "Bake Sale - CS Club" while the answer key says "CS Club Bake Sale". The spec has to say how the eval compares names, without editing the key.
- What counts as one item: a line like "2 x Blue book @ 1.25" is one item with quantity 2, which is how the answer key counts.

**Approved by:** Ralston Raphael, October 25, 2026
