"""Money arithmetic for invoices — subtotal, discounts, tax and grand total.

This module is the single source of truth for invoice totalling. Every amount is
a :class:`~decimal.Decimal`, and every figure that represents real money is
rounded to two decimal places using banker's-free, "round half up" rounding via
:data:`decimal.ROUND_HALF_UP` (the convention humans expect on receipts).

The computation order is deliberate and matches standard billing practice:

1.  **Line gross** = ``quantity * unit_price`` for each line.
2.  **Per-line discount** is subtracted from each line's gross.
3.  **Subtotal** is the sum of discounted line nets.
4.  **Invoice discount** is subtracted from the subtotal.
5.  **Tax** is ``tax_rate%`` of the post-discount taxable base.
6.  **Grand total** = taxable base + tax.

Part of Invoice Generator by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict

from invoice_generator.model import Discount, DiscountKind, Invoice, LineItem

CENTS = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Round a raw amount to two decimal places (cents), half-up.

    Args:
        value: An unrounded monetary amount.

    Returns:
        ``value`` quantized to two decimal places using ``ROUND_HALF_UP``.
    """
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(base: Decimal, discount: Discount | None) -> Decimal:
    """Return the discount amount for ``base`` (never larger than ``base``).

    A percentage discount is ``base * value / 100``; a fixed discount is the
    flat ``value``. The result is clamped to ``[0, base]`` so a discount can
    never make a line or invoice go negative, and is rounded to cents.

    Args:
        base: The amount the discount is applied against.
        discount: The discount to apply, or ``None`` for no discount.

    Returns:
        The (non-negative) money amount to subtract from ``base``.
    """
    if discount is None:
        return Decimal("0.00")
    if discount.kind is DiscountKind.PERCENT:
        raw = base * discount.value / Decimal(100)
    else:
        raw = discount.value
    amount = money(raw)
    if amount < Decimal("0.00"):
        return Decimal("0.00")
    return min(amount, money(base))


def line_gross(item: LineItem) -> Decimal:
    """Return ``quantity * unit_price`` for a line, rounded to cents."""
    return money(item.quantity * item.unit_price)


def line_net(item: LineItem) -> Decimal:
    """Return a line's total after its per-line discount, rounded to cents."""
    gross = line_gross(item)
    return gross - apply_discount(gross, item.discount)


class InvoiceTotals(BaseModel):
    """The computed money figures for an invoice. All values are in cents-exact Decimals.

    Attributes:
        subtotal: Sum of line nets (after per-line discounts, before invoice
            discount and tax).
        invoice_discount: Amount removed by the invoice-level discount.
        taxable_base: ``subtotal - invoice_discount``; the base tax applies to.
        tax: Tax charged on ``taxable_base``.
        grand_total: ``taxable_base + tax`` — the amount due.
    """

    model_config = ConfigDict(frozen=True)

    subtotal: Decimal
    invoice_discount: Decimal
    taxable_base: Decimal
    tax: Decimal
    grand_total: Decimal


def compute_totals(invoice: Invoice) -> InvoiceTotals:
    """Compute every money figure for an invoice with exact cent rounding.

    Args:
        invoice: The fully-populated invoice to total.

    Returns:
        An :class:`InvoiceTotals` with subtotal, discounts, tax and grand total.
    """
    subtotal = sum((line_net(item) for item in invoice.items), Decimal("0.00"))
    subtotal = money(subtotal)

    invoice_discount = apply_discount(subtotal, invoice.invoice_discount)
    taxable_base = subtotal - invoice_discount

    tax = money(taxable_base * invoice.tax_rate / Decimal(100))
    grand_total = taxable_base + tax

    return InvoiceTotals(
        subtotal=subtotal,
        invoice_discount=invoice_discount,
        taxable_base=taxable_base,
        tax=tax,
        grand_total=grand_total,
    )
