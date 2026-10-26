"""Reader tests: hand-written replies and a fake post_json. No key, no network."""

import io
import json
import urllib.error

import pytest

import reader
from models import Item, ReadFailure, Receipt, Usage

IMAGE = "images/receipt-01.png"

GOOD = {
    "merchant": "Mather Dining Hall",
    "date": "2026-10-02",
    "items": [
        {"name": "Blue book", "quantity": 2, "unit_price": 1.25},
        {"name": "Pen", "quantity": 1, "unit_price": 3.5},
    ],
    "subtotal": 6.0,
    "discount": 0,
    "tax": 0.42,
    "total": 6.42,
}
GOOD_TEXT = json.dumps(GOOD)
EXPECTED = Receipt(
    merchant="Mather Dining Hall",
    date="2026-10-02",
    items=[Item("Blue book", 2, 1.25), Item("Pen", 1, 3.5)],
    subtotal=6.0,
    discount=0,
    tax=0.42,
    total=6.42,
)


def without(key):
    return json.dumps({k: v for k, v in GOOD.items() if k != key})


def with_(**changes):
    return json.dumps({**GOOD, **changes})


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("CHAT_MODEL", "CHAT_REASONING", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


# Behavior 1: bare, fenced and prose-wrapped JSON give the same receipt

def test_bare_json():
    assert reader.parse_reply(GOOD_TEXT) == EXPECTED


def test_fenced_json():
    assert reader.parse_reply("```json\n" + GOOD_TEXT + "\n```") == EXPECTED


def test_plain_fence():
    assert reader.parse_reply("```\n" + GOOD_TEXT + "\n```") == EXPECTED


def test_prose_wrapped_json():
    text = "Here is the receipt you asked for:\n" + GOOD_TEXT + "\nHope that helps!"
    assert reader.parse_reply(text) == EXPECTED


def test_json_followed_by_text_with_braces():
    text = GOOD_TEXT + "\nNote: totals use the {printed} values, not {computed} ones."
    assert reader.parse_reply(text) == EXPECTED


def test_model_and_usage_are_kept():
    usage = Usage(10, 20)
    result = reader.parse_reply(GOOD_TEXT, model="m", usage=usage)
    assert result.model == "m"
    assert result.usage == usage


# Behavior 2: not JSON is a failed read

def test_not_json():
    result = reader.parse_reply("Sorry, I cannot read this image.")
    assert isinstance(result, ReadFailure)
    assert result.reason.startswith("the reply is not JSON:")
    assert "Sorry, I cannot read this image." in result.reason
    assert result.raw == "Sorry, I cannot read this image."


def test_not_json_reason_shows_only_80_chars():
    result = reader.parse_reply("x" * 200)
    assert result.reason == "the reply is not JSON: " + "x" * 80


def test_json_array_is_not_an_object():
    result = reader.parse_reply("[1, 2, 3]")
    assert isinstance(result, ReadFailure)
    assert result.reason.startswith("the reply is not JSON:")


def test_failure_keeps_model_and_usage():
    usage = Usage(3, 4)
    result = reader.parse_reply("nope", model="m", usage=usage)
    assert result.model == "m"
    assert result.usage == usage


# Behavior 3: wrong shapes name the field

def test_missing_total():
    result = reader.parse_reply(without("total"))
    assert isinstance(result, ReadFailure)
    assert "field 'total' is missing" in result.reason
    assert result.raw == without("total")


def test_missing_merchant():
    result = reader.parse_reply(without("merchant"))
    assert "field 'merchant' is missing" in result.reason


def test_items_not_a_list():
    result = reader.parse_reply(with_(items="Blue book"))
    assert isinstance(result, ReadFailure)
    assert "field 'items' is not a list" in result.reason


def test_item_missing_unit_price():
    items = [GOOD["items"][0], {"name": "Pen", "quantity": 1}]
    result = reader.parse_reply(with_(items=items))
    assert isinstance(result, ReadFailure)
    assert "field 'items[1].unit_price'" in result.reason


def test_item_unit_price_not_a_number():
    items = [GOOD["items"][0], {"name": "Pen", "quantity": 1, "unit_price": "3.50"}]
    result = reader.parse_reply(with_(items=items))
    assert "field 'items[1].unit_price' is not a number" in result.reason


def test_item_not_an_object():
    result = reader.parse_reply(with_(items=["Pen"]))
    assert isinstance(result, ReadFailure)
    assert "items[0]" in result.reason


def test_total_as_string_is_rejected():
    result = reader.parse_reply(with_(total="13.66"))
    assert isinstance(result, ReadFailure)
    assert "field 'total' is not a number" in result.reason


def test_bool_is_not_a_number():
    result = reader.parse_reply(with_(tax=True))
    assert "field 'tax' is not a number" in result.reason


def test_date_in_wrong_format():
    result = reader.parse_reply(with_(date="10/02/2026"))
    assert isinstance(result, ReadFailure)
    assert "field 'date' is not YYYY-MM-DD or null" in result.reason


def test_date_that_does_not_exist():
    result = reader.parse_reply(with_(date="2026-02-30"))
    assert "field 'date' is not YYYY-MM-DD or null" in result.reason


# Behavior 9: null date and missing discount/tax

def test_null_date_is_none():
    result = reader.parse_reply(with_(date=None))
    assert isinstance(result, Receipt)
    assert result.date is None


def test_missing_discount_and_tax_are_zero():
    data = {k: v for k, v in GOOD.items() if k not in ("discount", "tax")}
    result = reader.parse_reply(json.dumps(data))
    assert isinstance(result, Receipt)
    assert result.discount == 0
    assert result.tax == 0


def test_null_discount_and_tax_are_zero():
    result = reader.parse_reply(with_(discount=None, tax=None))
    assert isinstance(result, Receipt)
    assert result.discount == 0
    assert result.tax == 0


# Behavior 4: empty reply

def test_empty_reply_with_length():
    result = reader.parse_reply("", finish_reason="length")
    assert isinstance(result, ReadFailure)
    assert result.reason == (
        "the model used its whole output budget before answering (finish_reason: length)"
    )


def test_whitespace_reply_with_length():
    result = reader.parse_reply("  \n", finish_reason="length")
    assert "whole output budget" in result.reason


def test_empty_reply_otherwise():
    result = reader.parse_reply("", finish_reason="stop")
    assert result.reason == "the model returned an empty reply"


# Behavior 10: the request body

def image_part(body):
    return body["messages"][0]["content"][1]


def text_part(body):
    return body["messages"][0]["content"][0]


def test_request_has_image_instruction_and_model():
    body = reader.build_request(IMAGE, "xiaomi/mimo-v2.6-flash")
    assert body["model"] == "xiaomi/mimo-v2.6-flash"
    assert body["max_tokens"] == reader.MAX_TOKENS
    assert body["temperature"] == 0
    assert body["usage"] == {"include": True}
    message = body["messages"][0]
    assert message["role"] == "user"
    assert text_part(body) == {"type": "text", "text": reader.INSTRUCTION}
    assert image_part(body)["type"] == "image_url"
    assert image_part(body)["image_url"]["url"].startswith("data:image/png;base64,")


def test_image_data_round_trips():
    import base64

    url = image_part(reader.build_request(IMAGE, "m"))["image_url"]["url"]
    with open(IMAGE, "rb") as f:
        assert base64.b64decode(url.split(",", 1)[1]) == f.read()


def test_mime_from_extension(tmp_path):
    for ext, mime in ((".jpg", "image/jpeg"), (".jpeg", "image/jpeg"), (".webp", "image/webp")):
        path = tmp_path / ("x" + ext)
        path.write_bytes(b"abc")
        url = image_part(reader.build_request(str(path), "m"))["image_url"]["url"]
        assert url.startswith(f"data:{mime};base64,")


def test_instruction_content():
    text = reader.INSTRUCTION
    assert "without the address" in text
    assert "YYYY-MM-DD" in text
    assert "2 x Blue book @ 1.25" in text
    assert "arithmetic" not in text.lower()


def test_reasoning_off_for_mimo():
    body = reader.build_request(IMAGE, "xiaomi/mimo-v2.6-flash")
    assert body["reasoning"] == {"enabled": False}


def test_no_reasoning_key_for_minimax():
    body = reader.build_request(IMAGE, "minimax/minimax-m3")
    assert "reasoning" not in body


def test_chat_reasoning_on_removes_it_for_mimo(monkeypatch):
    monkeypatch.setenv("CHAT_REASONING", "on")
    body = reader.build_request(IMAGE, "xiaomi/mimo-v2.6-flash")
    assert "reasoning" not in body


def test_chat_reasoning_off_adds_it_for_minimax(monkeypatch):
    monkeypatch.setenv("CHAT_REASONING", "off")
    body = reader.build_request(IMAGE, "minimax/minimax-m3")
    assert body["reasoning"] == {"enabled": False}


def test_reasoning_enabled_table():
    assert reader.reasoning_enabled("xiaomi/mimo-v2.6-flash") is False
    assert reader.reasoning_enabled("minimax/minimax-m3") is True


# read_receipt with a fake post_json

def reply(content, finish="stop"):
    return 200, {
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": 1500, "completion_tokens": 120},
    }


def test_read_receipt_returns_receipt_with_usage(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def fake(url, body, headers, timeout):
        calls.append((url, body, headers, timeout))
        return reply("```json\n" + GOOD_TEXT + "\n```")

    monkeypatch.setattr(reader, "post_json", fake)
    result = reader.read_receipt(IMAGE)
    assert isinstance(result, Receipt)
    assert result.items == EXPECTED.items
    assert result.usage == Usage(1500, 120)
    assert result.model == reader.DEFAULT_MODEL
    assert len(calls) == 1
    url, body, headers, timeout = calls[0]
    assert url == reader.BASE_URL + "/chat/completions"
    assert url.endswith("/chat/completions")
    assert headers["Authorization"] == "Bearer test-key"
    assert body["model"] == reader.DEFAULT_MODEL
    assert timeout == 60


def test_read_receipt_uses_chat_model(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("CHAT_MODEL", "minimax/minimax-m3")
    seen = []
    monkeypatch.setattr(
        reader, "post_json", lambda u, b, h, t: seen.append(b) or reply(GOOD_TEXT)
    )
    result = reader.read_receipt(IMAGE)
    assert seen[0]["model"] == "minimax/minimax-m3"
    assert result.model == "minimax/minimax-m3"


def test_read_receipt_length_failure_keeps_usage(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(reader, "post_json", lambda u, b, h, t: reply("", "length"))
    result = reader.read_receipt(IMAGE)
    assert isinstance(result, ReadFailure)
    assert "whole output budget" in result.reason
    assert result.usage == Usage(1500, 120)


def test_http_402_is_a_failed_read(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    error_body = json.dumps({"error": {"message": "Insufficient credits"}}).encode()

    def fake(url, body, headers, timeout):
        raise urllib.error.HTTPError(url, 402, "Payment Required", {}, io.BytesIO(error_body))

    monkeypatch.setattr(reader, "post_json", fake)
    result = reader.read_receipt(IMAGE)
    assert isinstance(result, ReadFailure)
    assert result.reason.startswith("HTTP 402")
    assert "Insufficient credits" in result.reason


def test_http_error_without_json_body(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake(url, body, headers, timeout):
        raise urllib.error.HTTPError(url, 502, "Bad Gateway", {}, io.BytesIO(b"<html>"))

    monkeypatch.setattr(reader, "post_json", fake)
    result = reader.read_receipt(IMAGE)
    assert isinstance(result, ReadFailure)
    assert result.reason.startswith("HTTP 502")


@pytest.mark.parametrize(
    "exc",
    [TimeoutError(), urllib.error.URLError(TimeoutError("timed out"))],
)
def test_timeout_is_a_failed_read(monkeypatch, exc):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake(url, body, headers, timeout):
        raise exc

    monkeypatch.setattr(reader, "post_json", fake)
    result = reader.read_receipt(IMAGE)
    assert isinstance(result, ReadFailure)
    assert result.reason == "the model did not answer within 60 s"


def test_no_key_raises_and_makes_no_request(monkeypatch):
    called = []
    monkeypatch.setattr(reader, "post_json", lambda *a: called.append(a))
    with pytest.raises(reader.MissingKey):
        reader.read_receipt(IMAGE)
    assert called == []
