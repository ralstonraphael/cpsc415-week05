"""Behavior 2 and 11 at the command line: exit codes and output, with the network faked."""

import json

import pytest

import reader
import receipts

IMAGE = "images/receipt-01.png"
CONSISTENT = {
    "merchant": "Mather Dining Hall", "date": "2026-10-02",
    "items": [{"name": "Lunch", "quantity": 1, "unit_price": 10.50},
              {"name": "Soup", "quantity": 1, "unit_price": 1.75},
              {"name": "Lemonade", "quantity": 1, "unit_price": 0.60}],
    "subtotal": 12.85, "discount": 0, "tax": 0.81, "total": 13.66,
}


@pytest.fixture
def fake_post(monkeypatch):
    """Replace the one network function. Set .content to the model's reply text."""
    calls = []

    def post(url, body, headers, timeout):
        calls.append(url)
        return 200, {"choices": [{"message": {"content": post.content}, "finish_reason": "stop"}],
                     "usage": {"prompt_tokens": 500, "completion_tokens": 200}}

    post.content = json.dumps(CONSISTENT)
    post.calls = calls
    monkeypatch.setattr(reader, "post_json", post)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    return post


def test_no_key_exits_2_without_a_request(fake_post, monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY")
    assert receipts.main([IMAGE]) == 2
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err
    assert fake_post.calls == []


def test_consistent_receipt_prints_json_and_no_problems(fake_post, capsys):
    assert receipts.main([IMAGE]) == 0
    out = capsys.readouterr().out
    assert '"merchant": "Mather Dining Hall"' in out
    assert "No problems." in out


def test_inconsistent_receipt_lists_the_problem(fake_post, capsys):
    fake_post.content = json.dumps({**CONSISTENT, "total": 14.66})
    assert receipts.main([IMAGE]) == 0
    out = capsys.readouterr().out
    assert "Problems:" in out
    assert "subtotal - discount + tax is $13.66 but the total is $14.66 (off by $1.00)" in out


def test_reply_that_is_not_json_is_a_failed_read(fake_post, capsys):
    fake_post.content = "Sorry, I can't read this receipt."
    assert receipts.main([IMAGE]) == 1
    assert capsys.readouterr().out.startswith("Failed read: the reply is not JSON")


def test_missing_image_exits_1(fake_post, capsys):
    assert receipts.main(["images/no-such-receipt.png"]) == 1
    assert "no-such-receipt.png" in capsys.readouterr().err
    assert fake_post.calls == []
