"""Behavior 12: read every image in RECEIPT_DIR with the real model and compare with its expected.json.

  OPENROUTER_API_KEY=... python -m pytest -m eval -v                      # images/, default model
  CHAT_MODEL=minimax/minimax-m3 python -m pytest -m eval -v               # the other model
  RECEIPT_DIR=my-receipts python -m pytest -m eval -v                     # your own receipts
"""

import json
import os
from pathlib import Path

import pytest

import reader
from checker import check
from merchant import same_merchant
from models import ReadFailure

ROOT = Path(__file__).resolve().parent.parent
RECEIPT_DIR = ROOT / os.environ.get("RECEIPT_DIR", "images")
EXPECTED = json.loads((RECEIPT_DIR / "expected.json").read_text())
IMAGES = sorted(EXPECTED)

pytestmark = [
    pytest.mark.eval,
    pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="needs OPENROUTER_API_KEY"),
]


@pytest.fixture(scope="session")
def read():
    """One model call per image for the whole run; every test for that image reuses it."""
    cache = {}

    def get(name):
        if name not in cache:
            cache[name] = reader.read_receipt(RECEIPT_DIR / name)
        result = cache[name]
        if isinstance(result, ReadFailure):
            pytest.fail(f"failed read: {result.reason}")
        return result

    return get


def cents(amount):
    return round(amount * 100)


@pytest.mark.parametrize("name", IMAGES)
def test_total(read, name):
    assert cents(read(name).total) == cents(EXPECTED[name]["total"])


@pytest.mark.parametrize("name", IMAGES)
def test_item_count(read, name):
    assert len(read(name).items) == EXPECTED[name]["items"]


@pytest.mark.parametrize("name", IMAGES)
def test_merchant(read, name):
    assert same_merchant(read(name).merchant, EXPECTED[name]["merchant"]), read(name).merchant


@pytest.mark.parametrize("name", IMAGES)
def test_date(read, name):
    assert read(name).date == EXPECTED[name]["date"]


@pytest.mark.parametrize("name", IMAGES)
def test_checker_clean(read, name):
    assert check(read(name)) == []
