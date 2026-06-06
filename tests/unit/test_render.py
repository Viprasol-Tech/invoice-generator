"""Tests that rendered invoices contain the correct totals and escape input."""

from __future__ import annotations

from decimal import Decimal

from invoice_generator.cli import sample_invoice
from invoice_generator.model import Invoice, LineItem, Party
from invoice_generator.render import render_html, render_text


def test_text_render_contains_totals() -> None:
    text = render_text(sample_invoice())
    assert "INVOICE INV-2025-0007" in text
    assert "Subtotal" in text
    assert "USD 4,878.00" in text  # subtotal
    assert "USD 860.04" in text  # tax
    assert "GRAND TOTAL" in text
    assert "USD 5,638.04" in text  # grand total


def test_html_render_contains_totals_and_is_document() -> None:
    html = render_html(sample_invoice())
    assert html.startswith("<!doctype html>")
    assert "4,878.00" in html
    assert "860.04" in html
    assert "5,638.04" in html
    assert "</html>" in html


def test_html_escapes_user_input() -> None:
    inv = Invoice(
        number="INV-2",
        seller=Party(name="<script>alert(1)</script>"),
        buyer=Party(name="Buyer & Co"),
        items=[LineItem(description="a & b", quantity=Decimal("1"), unit_price=Decimal("1.00"))],
    )
    html = render_html(inv)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Buyer &amp; Co" in html
    assert "a &amp; b" in html
