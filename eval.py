"""Print the eval as a markdown table for CHECKS.md: the same comparisons as tests/test_eval.py,
plus tokens and the strict merchant compare we did not choose.

  OPENROUTER_API_KEY=... python eval.py
  CHAT_MODEL=minimax/minimax-m3 python eval.py
  RECEIPT_DIR=my-receipts python eval.py
"""

import json
import os
from pathlib import Path

import reader
from checker import check
from merchant import same_merchant, strict_merchant
from models import ReadFailure


def mark(ok, got=None):
    return "pass" if ok else f"**FAIL** ({got})" if got is not None else "**FAIL**"


def main():
    receipt_dir = Path(os.environ.get("RECEIPT_DIR", "images"))
    expected = json.loads((receipt_dir / "expected.json").read_text())
    model = os.environ.get("CHAT_MODEL") or reader.DEFAULT_MODEL
    reasoning = "on" if reader.reasoning_enabled(model) else "off"
    print(f"Model `{model}`, reasoning {reasoning}, receipts in `{receipt_dir}/`\n")
    print("| Receipt | Total | Items | Merchant (word set / strict) | Date | Checker | Tokens in / out |")
    print("|---|---|---|---|---|---|---|")

    passed = calls = tokens_in = tokens_out = 0
    for name, want in expected.items():
        result = reader.read_receipt(receipt_dir / name)  # one call per image
        calls += 1
        tokens_in += result.usage.prompt_tokens
        tokens_out += result.usage.completion_tokens
        tokens = f"{result.usage.prompt_tokens} / {result.usage.completion_tokens}"
        if isinstance(result, ReadFailure):
            print(f"| {name} | failed read: {result.reason} | | | | | {tokens} |")
            continue

        checks = {
            "total": round(result.total * 100) == round(want["total"] * 100),
            "items": len(result.items) == want["items"],
            "merchant": same_merchant(result.merchant, want["merchant"]),
            "date": result.date == want["date"],
            "checker": not check(result),
        }
        passed += sum(checks.values())
        strict = "pass" if strict_merchant(result.merchant, want["merchant"]) else "FAIL"
        problems = check(result)
        print(
            f"| {name} | {mark(checks['total'], result.total)} | {mark(checks['items'], len(result.items))} "
            f"| {mark(checks['merchant'], result.merchant)} / {strict} | {mark(checks['date'], result.date)} "
            f"| {'clean' if not problems else '; '.join(problems)} | {tokens} |"
        )

    print(f"\n{passed} of {5 * len(expected)} checks passed. {calls} model calls, "
          f"{tokens_in} tokens in, {tokens_out} out.")


if __name__ == "__main__":
    main()
