"""Arithmetic check on a Receipt: returns a list of plain-sentence problems."""

from models import Receipt


def cents(x: float) -> int:
    return round(x * 100)


def money(c: int) -> str:
    """Whole cents as dollars: 1366 -> '$13.66', -115 -> '-$1.15'."""
    return f"{'-' if c < 0 else ''}${abs(c) // 100}.{abs(c) % 100:02d}"


def check(receipt: Receipt) -> list[str]:
    """Return every problem found; an empty list means none. Never edits the receipt."""
    problems = []
    if not receipt.items:
        problems.append("the receipt has no items")
    for item in receipt.items:
        if item.quantity < 0:
            problems.append(f"item '{item.name}' has a negative quantity: {item.quantity:g}")
        if item.unit_price < 0:
            problems.append(
                f"item '{item.name}' has a negative unit price: {money(cents(item.unit_price))}"
            )
    if receipt.discount < 0:
        problems.append(
            f"discount is negative: {money(cents(receipt.discount))} "
            "(write it as a positive amount that is subtracted)"
        )
    if receipt.tax < 0:
        problems.append(f"tax is negative: {money(cents(receipt.tax))}")

    items = sum(cents(i.quantity * i.unit_price) for i in receipt.items)
    subtotal = cents(receipt.subtotal)
    if items != subtotal:
        problems.append(
            f"items add up to {money(items)} but the subtotal is {money(subtotal)} "
            f"(off by {money(abs(items - subtotal))})"
        )

    expected = subtotal - cents(receipt.discount) + cents(receipt.tax)
    total = cents(receipt.total)
    if expected != total:
        problems.append(
            f"subtotal - discount + tax is {money(expected)} but the total is {money(total)} "
            f"(off by {money(abs(expected - total))})"
        )
    return problems
