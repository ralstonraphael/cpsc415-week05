"""Read one receipt photo and check its arithmetic.

  export OPENROUTER_API_KEY=...        # never committed
  python receipts.py images/receipt-01.png
  CHAT_MODEL=minimax/minimax-m3 python receipts.py images/receipt-01.png

Exit status: 0 read (with or without problems), 1 failed read or missing image, 2 no key.
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

import reader
from checker import check
from models import ReadFailure


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python receipts.py PHOTO", file=sys.stderr)
        return 1
    path = Path(args[0])
    if not path.is_file():
        print(f"No such image: {path}", file=sys.stderr)
        return 1

    try:
        result = reader.read_receipt(path)
    except reader.MissingKey:
        print("OPENROUTER_API_KEY is not set. Run: export OPENROUTER_API_KEY=<your key>", file=sys.stderr)
        return 2
    if isinstance(result, ReadFailure):
        print(f"Failed read: {result.reason}")
        return 1

    fields = asdict(result)
    usage = fields.pop("usage")
    model = fields.pop("model")
    print(json.dumps(fields, indent=2))
    print(f"(read by {model}: {usage['prompt_tokens']} tokens in, {usage['completion_tokens']} out)")

    problems = check(result)  # our code decides whether the numbers add up, not the model
    if problems:
        print("Problems:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("No problems.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
