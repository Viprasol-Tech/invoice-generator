"""Render invoices to plain text and minimal HTML — no template engine.

Both renderers call :func:`invoice_generator.calc.compute_totals` so the figures
shown always match the canonical arithmetic. The HTML renderer escapes all
user-supplied strings to keep the output injection-safe, and uses only inline
markup so the result is a self-contained document with no external assets.

Part of Invoice Generator by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from decimal import Decimal
from html import escape

from invoice_generator.calc import compute_totals, line_gross, line_net
from invoice_generator.model import Discount, DiscountKind, Invoice, LineItem


def _fmt(amount: Decimal, currency: str) -> str:
    """Format a cent-exact amount with its currency code, e.g. ``USD 1,234.50``."""
    return f"{currency} {amount:,.2f}"


def _discount_label(discount: Discount | None) -> str:
    """Return a short human label for a discount, e.g. ``-10%`` or ``-USD 5.00``."""
    if discount is None:
        return ""
    if discount.kind is DiscountKind.PERCENT:
        return f"-{discount.value.normalize():f}%"
    return f"-{discount.value:,.2f}"


def render_text(invoice: Invoice) -> str:
    """Render an invoice as a fixed-width plain-text document.

    Args:
        invoice: The invoice to render.

    Returns:
        A multi-line string suitable for printing to a terminal or a ``.txt``
        file. Contains the line items, all discounts, the tax line and the
        grand total.
    """
    totals = compute_totals(invoice)
    cur = invoice.currency
    width = 64
    lines: list[str] = []

    lines.append("=" * width)
    lines.append(f"INVOICE {invoice.number}".center(width))
    lines.append("=" * width)
    lines.append(f"From: {invoice.seller.name}")
    if invoice.seller.address:
        lines.append(f"      {invoice.seller.address}")
    lines.append(f"To:   {invoice.buyer.name}")
    if invoice.buyer.address:
        lines.append(f"      {invoice.buyer.address}")
    lines.append("-" * width)
    lines.append(f"{'Description':<30}{'Qty':>6}{'Unit':>12}{'Amount':>16}")
    lines.append("-" * width)

    for item in invoice.items:
        gross = line_gross(item)
        lines.append(
            f"{item.description[:30]:<30}"
            f"{item.quantity.normalize():>6f}"
            f"{item.unit_price:>12,.2f}"
            f"{gross:>16,.2f}"
        )
        if item.discount is not None:
            net = line_net(item)
            note = f"  discount {_discount_label(item.discount)}"
            lines.append(f"{note:<48}{net:>16,.2f}")

    lines.append("-" * width)
    lines.append(f"{'Subtotal':<48}{_fmt(totals.subtotal, cur):>16}")
    if invoice.invoice_discount is not None:
        label = f"Invoice discount {_discount_label(invoice.invoice_discount)}"
        lines.append(f"{label:<48}{('-' + _fmt(totals.invoice_discount, cur)):>16}")
    lines.append(f"{f'Tax ({invoice.tax_rate.normalize():f}%)':<48}{_fmt(totals.tax, cur):>16}")
    lines.append("=" * width)
    lines.append(f"{'GRAND TOTAL':<48}{_fmt(totals.grand_total, cur):>16}")
    lines.append("=" * width)

    if invoice.notes:
        lines.append("")
        lines.append(f"Notes: {invoice.notes}")

    return "\n".join(lines)


def _html_row(item: LineItem) -> str:
    """Render a single line item as an HTML table row."""
    net = line_net(item)
    disc = ""
    if item.discount is not None:
        disc = escape(_discount_label(item.discount))
    return (
        "<tr>"
        f"<td>{escape(item.description)}</td>"
        f"<td class='num'>{item.quantity.normalize():f}</td>"
        f"<td class='num'>{item.unit_price:,.2f}</td>"
        f"<td class='num'>{disc}</td>"
        f"<td class='num'>{net:,.2f}</td>"
        "</tr>"
    )


def render_html(invoice: Invoice) -> str:
    """Render an invoice as a minimal, self-contained HTML document.

    All user-supplied text is HTML-escaped. The document uses only a small
    inline ``<style>`` block, so it renders identically with no network access.

    Args:
        invoice: The invoice to render.

    Returns:
        A complete HTML document string containing the line items and totals.
    """
    totals = compute_totals(invoice)
    cur = escape(invoice.currency)
    rows = "\n".join(_html_row(item) for item in invoice.items)

    discount_row = ""
    if invoice.invoice_discount is not None:
        discount_row = (
            "<tr><th colspan='4'>Invoice discount "
            f"{escape(_discount_label(invoice.invoice_discount))}</th>"
            f"<td class='num'>-{totals.invoice_discount:,.2f}</td></tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Invoice {escape(invoice.number)}</title>
<style>
  body {{ font-family: system-ui, Arial, sans-serif; margin: 2rem; color: #1a1a1a; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .parties {{ display: flex; gap: 3rem; margin: 1rem 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem; border-bottom: 1px solid #ddd; text-align: left; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tfoot th {{ text-align: right; border-bottom: none; }}
  tfoot td {{ text-align: right; border-bottom: none; font-weight: 600; }}
  .grand td, .grand th {{ font-size: 1.1rem; border-top: 2px solid #1a1a1a; }}
</style>
</head>
<body>
<h1>Invoice {escape(invoice.number)}</h1>
<div class="parties">
  <div><strong>From</strong><br>{escape(invoice.seller.name)}<br>
    {escape(invoice.seller.address)}</div>
  <div><strong>To</strong><br>{escape(invoice.buyer.name)}<br>
    {escape(invoice.buyer.address)}</div>
</div>
<table>
<thead>
<tr><th>Description</th><th class="num">Qty</th><th class="num">Unit</th>
    <th class="num">Discount</th><th class="num">Amount ({cur})</th></tr>
</thead>
<tbody>
{rows}
</tbody>
<tfoot>
<tr><th colspan="4">Subtotal</th><td class="num">{totals.subtotal:,.2f}</td></tr>
{discount_row}
<tr><th colspan="4">Tax ({invoice.tax_rate.normalize():f}%)</th>
    <td class="num">{totals.tax:,.2f}</td></tr>
<tr class="grand"><th colspan="4">Grand total ({cur})</th>
    <td class="num">{totals.grand_total:,.2f}</td></tr>
</tfoot>
</table>
{f"<p>{escape(invoice.notes)}</p>" if invoice.notes else ""}
</body>
</html>"""
