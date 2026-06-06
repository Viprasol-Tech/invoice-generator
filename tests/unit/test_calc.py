"""Correctness tests for invoice money arithmetic (exact Decimal values)."""

from __future__ import annotations

from decimal import Decimal

from invoice_generator.calc import (
    apply_discount,
    compute_totals,
    line_gross,
    line_net,
    money,
)
from invoice_generator.model import Discount, Invoice, LineItem, Party


def _party() -> Party:
    return Party(name="Seller")


def _invoice(items: list[LineItem], **kw: object) -> Invoice:
    return Invoice(number="INV-1", seller=_party(), buyer=Party(name="Buyer"), items=items, **kw)


def test_money_rounds_half_up_to_cents() -> None:
    assert money(Decimal("1.005")) == Decimal("1.01")
    assert money(Decimal("1.004")) == Decimal("1.00")
    assert money(Decimal("2.675")) == Decimal("2.68")


def test_line_gross_and_net_without_discount() -> None:
    item = LineItem(description="x", quantity=Decimal("3"), unit_price=Decimal("9.99"))
    assert line_gross(item) == Decimal("29.97")
    assert line_net(item) == Decimal("29.97")


def test_percent_discount_on_line() -> None:
    item = LineItem(
        description="x",
        quantity=Decimal("24"),
        unit_price=Decimal("80.00"),
        discount=Discount.percent(10),
    )
    # gross 1920.00, 10% = 192.00, net 1728.00
    assert line_gross(item) == Decimal("1920.00")
    assert line_net(item) == Decimal("1728.00")


def test_fixed_discount_on_line() -> None:
    item = LineItem(
        description="x",
        quantity=Decimal("1"),
        unit_price=Decimal("180.00"),
        discount=Discount.fixed("30.00"),
    )
    assert line_net(item) == Decimal("150.00")


def test_apply_discount_is_clamped_to_base() -> None:
    # A fixed discount larger than the base never goes negative.
    assert apply_discount(Decimal("50.00"), Discount.fixed("999.00")) == Decimal("50.00")
    assert apply_discount(Decimal("50.00"), None) == Decimal("0.00")


def test_zero_tax_invoice() -> None:
    inv = _invoice(
        [LineItem(description="a", quantity=Decimal("2"), unit_price=Decimal("10.00"))],
        tax_rate=Decimal("0"),
    )
    totals = compute_totals(inv)
    assert totals.subtotal == Decimal("20.00")
    assert totals.tax == Decimal("0.00")
    assert totals.grand_total == Decimal("20.00")


def test_tax_rounds_to_cents() -> None:
    # 33.33 * 18% = 5.9994 -> rounds to 6.00
    inv = _invoice(
        [LineItem(description="a", quantity=Decimal("1"), unit_price=Decimal("33.33"))],
        tax_rate=Decimal("18"),
    )
    totals = compute_totals(inv)
    assert totals.subtotal == Decimal("33.33")
    assert totals.tax == Decimal("6.00")
    assert totals.grand_total == Decimal("39.33")


def test_full_invoice_known_values() -> None:
    inv = _invoice(
        [
            LineItem(description="Backend", quantity=Decimal("40"), unit_price=Decimal("75.00")),
            LineItem(
                description="Frontend",
                quantity=Decimal("24"),
                unit_price=Decimal("80.00"),
                discount=Discount.percent(10),
            ),
            LineItem(
                description="Hosting",
                quantity=Decimal("1"),
                unit_price=Decimal("180.00"),
                discount=Discount.fixed("30.00"),
            ),
        ],
        tax_rate=Decimal("18"),
        invoice_discount=Discount.fixed("100.00"),
    )
    totals = compute_totals(inv)
    # 3000 + 1728 + 150 = 4878.00
    assert totals.subtotal == Decimal("4878.00")
    assert totals.invoice_discount == Decimal("100.00")
    assert totals.taxable_base == Decimal("4778.00")
    # 4778.00 * 18% = 860.04
    assert totals.tax == Decimal("860.04")
    assert totals.grand_total == Decimal("5638.04")


def test_invoice_percent_discount() -> None:
    inv = _invoice(
        [LineItem(description="a", quantity=Decimal("1"), unit_price=Decimal("200.00"))],
        tax_rate=Decimal("10"),
        invoice_discount=Discount.percent(25),
    )
    totals = compute_totals(inv)
    assert totals.subtotal == Decimal("200.00")
    assert totals.invoice_discount == Decimal("50.00")
    assert totals.taxable_base == Decimal("150.00")
    assert totals.tax == Decimal("15.00")
    assert totals.grand_total == Decimal("165.00")
