"""Shared data types: what the reader returns and the checker reads. No logic."""

from dataclasses import dataclass, field


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class Item:
    name: str
    quantity: float
    unit_price: float


@dataclass
class Receipt:
    merchant: str
    date: str | None  # "YYYY-MM-DD", or None when the year is not printed
    items: list[Item]
    subtotal: float
    discount: float  # a positive amount that is subtracted
    tax: float
    total: float
    model: str = ""
    usage: Usage = field(default_factory=Usage)


@dataclass
class ReadFailure:
    """The model's reply could not be turned into a Receipt. `reason` says why."""

    reason: str
    model: str = ""
    usage: Usage = field(default_factory=Usage)
    raw: str = ""
