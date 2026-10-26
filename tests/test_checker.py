"""Checker tests: hand-written receipts, no key and no network."""

import copy

from checker import check
from models import Item, Receipt


def make(items, subtotal, total, discount=0.0, tax=0.0):
    """Build a receipt from (name, quantity, unit_price) tuples."""
    return Receipt(
        merchant="Test Shop",
        date="2026-01-15",
        items=[Item(*i) for i in items],
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        total=total,
    )


def test_consistent_receipt_has_no_problems():
    r = make([("Notebook", 2, 3.50), ("Pen", 1, 1.25)], subtotal=8.25, tax=0.66, total=8.91)
    assert check(r) == []


def test_items_not_matching_subtotal():
    r = make([("Notebook", 2, 3.50), ("Pen", 1, 1.25)], subtotal=9.00, total=9.00)
    assert check(r) == ["items add up to $8.25 but the subtotal is $9.00 (off by $0.75)"]


def test_total_one_dollar_too_high():
    r = make([("Notebook", 2, 3.50)], subtotal=7.00, tax=0.50, total=8.50)
    assert check(r) == [
        "subtotal - discount + tax is $7.50 but the total is $8.50 (off by $1.00)"
    ]


def test_both_problems_at_once_in_order():
    r = make([("Notebook", 2, 3.50)], subtotal=8.00, tax=0.50, total=9.50)
    assert check(r) == [
        "items add up to $7.00 but the subtotal is $8.00 (off by $1.00)",
        "subtotal - discount + tax is $8.50 but the total is $9.50 (off by $1.00)",
    ]


def test_exactly_one_cent_off_is_reported():
    r = make([("Notebook", 1, 3.50)], subtotal=3.51, total=3.51)
    assert check(r) == ["items add up to $3.50 but the subtotal is $3.51 (off by $0.01)"]


def test_float_noise_is_not_reported():
    r = make([("A", 1, 0.1), ("B", 1, 0.2)], subtotal=0.3, total=0.3)
    assert check(r) == []


def test_amounts_are_rounded_not_truncated():
    """0.29 * 100 is 28.999999999999996: truncating it would make 0.29 + 0.71 come to $0.99."""
    r = make([("Gum", 1, 0.29), ("Mints", 1, 0.71)], subtotal=1.00, total=1.00)
    assert check(r) == []


def test_quantity_times_price_rounds_to_the_cent():
    r = make([("Gel pen", 3, 0.89)], subtotal=2.67, total=2.67)
    assert check(r) == []


def test_consistent_discount_receipt():
    r = make([("Binder", 1, 12.16)], subtotal=12.16, discount=1.15, tax=0.0, total=11.01)
    assert check(r) == []


def test_negative_discount_is_reported():
    r = make([("Binder", 1, 10.00)], subtotal=10.00, discount=-2.00, total=12.00)
    assert check(r) == [
        "discount is negative: -$2.00 (write it as a positive amount that is subtracted)"
    ]


def test_negative_tax_is_reported():
    r = make([("Binder", 1, 10.00)], subtotal=10.00, tax=-0.50, total=9.50)
    assert check(r) == ["tax is negative: -$0.50"]


def test_negative_quantity_is_reported():
    r = make([("Gel pen", -3, 0.89)], subtotal=-2.67, total=-2.67)
    assert check(r) == ["item 'Gel pen' has a negative quantity: -3"]


def test_negative_unit_price_is_reported():
    r = make([("Gel pen", 3, -0.89)], subtotal=-2.67, total=-2.67)
    assert check(r) == ["item 'Gel pen' has a negative unit price: -$0.89"]


def test_empty_items_is_reported():
    r = make([], subtotal=0.0, total=0.0)
    assert check(r) == ["the receipt has no items"]


def test_check_does_not_change_the_receipt():
    r = make([("Gel pen", -3, 0.89)], subtotal=5.00, discount=-1.00, tax=-0.10, total=9.00)
    before = copy.deepcopy(r)
    check(r)
    assert r == before
