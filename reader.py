"""Reader: send a receipt image to the chat endpoint, return a Receipt or a ReadFailure."""

import base64
import json
import os
import re
import socket
import urllib.error
import urllib.request
from datetime import date as _date

from models import Item, ReadFailure, Receipt, Usage

DEFAULT_MODEL = "xiaomi/mimo-v2.6-flash"
BASE_URL = os.environ.get("CHAT_BASE_URL", "https://openrouter.ai/api/v1")
REASONING_OFF = {"xiaomi/mimo-v2.6-flash"}  # models that must be told not to think
TIMEOUT_S = 60
MAX_TOKENS = 2000

INSTRUCTION = (
    "Read this receipt and reply with ONLY one JSON object, no other text: "
    '{"merchant": string, "date": string or null, '
    '"items": [{"name": string, "quantity": number, "unit_price": number}], '
    '"subtotal": number, "discount": number, "tax": number, "total": number}. '
    "merchant is the business name only, as printed, without the address. "
    "date is YYYY-MM-DD, or null when the year is not printed; "
    "a two-digit year means 20YY. "
    'A line like "2 x Blue book @ 1.25" is one item with quantity 2 and unit_price 1.25. '
    "discount is a positive amount that is subtracted. "
    "discount and tax are 0 when absent. "
    "subtotal is the items total when no subtotal line is printed."
)

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


class MissingKey(Exception):
    """OPENROUTER_API_KEY is not set."""


def reasoning_enabled(model):
    """CHAT_REASONING=on|off wins; otherwise reasoning is on unless the model is in the table."""
    setting = os.environ.get("CHAT_REASONING", "").lower()
    if setting in ("on", "off"):
        return setting == "on"
    return model not in REASONING_OFF


def build_request(image_path, model):
    """The JSON body: the fixed instruction plus the image as a base64 data URL."""
    mime = MIME.get(os.path.splitext(image_path)[1].lower(), "image/png")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    body = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "usage": {"include": True},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": INSTRUCTION},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}},
                ],
            }
        ],
    }
    if not reasoning_enabled(model):
        body["reasoning"] = {"enabled": False}
    return body


def extract_json(text):
    """The first JSON object in the text, ignoring ``` fences and any prose around it."""
    text = re.sub(r"```(?:json)?", "", text)
    decoder = json.JSONDecoder()
    for start, char in enumerate(text):
        if char == "{":
            try:
                value, _ = decoder.raw_decode(text, start)
            except ValueError:
                continue
            if isinstance(value, dict):
                return value
    return None


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_number(data, key, path, optional=False):
    """Return (value, None) or (None, reason) for one numeric field."""
    if key not in data or (optional and data[key] is None):
        return (0, None) if optional else (None, f"field '{path}' is missing")
    if not _is_number(data[key]):
        return None, f"field '{path}' is not a number"
    return data[key], None


def _valid_date(value):
    """None (year not printed) or a real calendar date written YYYY-MM-DD."""
    if value is None:
        return True
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        _date.fromisoformat(value)
        return True
    except ValueError:  # e.g. 2026-02-30
        return False


def _shape(data):
    """Validate the decoded object. Returns (Receipt fields, None) or (None, reason)."""
    if not isinstance(data.get("merchant"), str):
        why = "is missing" if "merchant" not in data else "is not text"
        return None, f"field 'merchant' {why}"
    when = data.get("date")
    if not _valid_date(when):
        return None, "field 'date' is not YYYY-MM-DD or null"
    if "items" not in data:
        return None, "field 'items' is missing"
    if not isinstance(data["items"], list):
        return None, "field 'items' is not a list"
    items = []
    for i, raw in enumerate(data["items"]):
        if not isinstance(raw, dict):
            return None, f"field 'items[{i}]' is not an object"
        if not isinstance(raw.get("name"), str):
            why = "is missing" if "name" not in raw else "is not text"
            return None, f"field 'items[{i}].name' {why}"
        qty, why = _check_number(raw, "quantity", f"items[{i}].quantity")
        if why:
            return None, why
        price, why = _check_number(raw, "unit_price", f"items[{i}].unit_price")
        if why:
            return None, why
        items.append(Item(raw["name"], qty, price))
    nums = {}
    for key in ("subtotal", "total"):
        nums[key], why = _check_number(data, key, key)
        if why:
            return None, why
    for key in ("discount", "tax"):
        nums[key], why = _check_number(data, key, key, optional=True)
        if why:
            return None, why
    return (data["merchant"], when, items, nums), None


def parse_reply(text, finish_reason="stop", model="", usage=None):
    """Turn the model's text into a Receipt, or a ReadFailure saying why. Never raises."""
    usage = usage or Usage()

    def fail(reason):
        return ReadFailure(reason, model=model, usage=usage, raw=text or "")

    if not text or not text.strip():
        if finish_reason == "length":
            return fail(
                "the model used its whole output budget before answering "
                "(finish_reason: length)"
            )
        return fail("the model returned an empty reply")
    data = extract_json(text)
    if data is None:
        return fail("the reply is not JSON: " + text.strip()[:80])
    parts, reason = _shape(data)
    if reason:
        return fail(reason)
    merchant, when, items, nums = parts
    return Receipt(
        merchant=merchant,
        date=when,
        items=items,
        subtotal=nums["subtotal"],
        discount=nums["discount"],
        tax=nums["tax"],
        total=nums["total"],
        model=model,
        usage=usage,
    )


def post_json(url, body, headers, timeout):
    """POST a JSON body and return (status, decoded reply). The only network call."""
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read())


def _is_timeout(exc):
    inner = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    return isinstance(inner, (socket.timeout, TimeoutError))


def read_receipt(image_path, model=None):
    """Read one receipt image. Raises MissingKey before any request if there is no key."""
    model = model or os.environ.get("CHAT_MODEL") or DEFAULT_MODEL
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise MissingKey("OPENROUTER_API_KEY is not set")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        _, reply = post_json(
            f"{BASE_URL}/chat/completions", build_request(image_path, model), headers, TIMEOUT_S
        )
    except urllib.error.HTTPError as exc:
        message = exc.reason
        try:
            message = json.loads(exc.read())["error"]["message"]
        except (ValueError, KeyError, TypeError):
            pass
        return ReadFailure(f"HTTP {exc.code}: {message}", model=model)
    except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
        if _is_timeout(exc):
            return ReadFailure(f"the model did not answer within {TIMEOUT_S} s", model=model)
        return ReadFailure(f"could not reach the endpoint: {exc}", model=model)

    raw_usage = reply.get("usage") or {}
    usage = Usage(raw_usage.get("prompt_tokens", 0), raw_usage.get("completion_tokens", 0))
    try:
        choice = reply["choices"][0]
        text = choice["message"].get("content") or ""
        finish = choice.get("finish_reason") or "stop"
    except (KeyError, IndexError, TypeError, AttributeError):
        return ReadFailure("the reply has no choices", model=model, usage=usage, raw=str(reply)[:200])
    return parse_reply(text, finish, model, usage)
