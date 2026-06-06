"""Command-line interface for Invoice Generator.

``invoice-generator demo`` builds a realistic sample invoice entirely offline,
totals it with exact ``Decimal`` arithmetic, and prints it as text or HTML.

Part of Invoice Generator by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from decimal import Decimal

import typer
from rich.console import Console

from invoice_generator import __version__
from invoice_generator.calc import compute_totals
from invoice_generator.model import Discount, Invoice, LineItem, Party
from invoice_generator.render import render_html, render_text

app = typer.Typer(add_completion=False, help="Invoice Generator — by Viprasol Tech.")
console = Console()


def sample_invoice() -> Invoice:
    """Build a representative sample invoice used by the demo command."""
    return Invoice(
        number="INV-2025-0007",
        seller=Party(
            name="Viprasol Tech Private Limited",
            address="Bengaluru, India",
            email="support@viprasol.com",
        ),
        buyer=Party(name="Acme Corp", address="123 Market St, Springfield"),
        items=[
            LineItem(
                description="Backend development",
                quantity=Decimal("40"),
                unit_price=Decimal("75.00"),
            ),
            LineItem(
                description="Frontend development",
                quantity=Decimal("24"),
                unit_price=Decimal("80.00"),
                discount=Discount.percent(10, label="loyalty"),
            ),
            LineItem(
                description="Domain & hosting (annual)",
                quantity=Decimal("1"),
                unit_price=Decimal("180.00"),
                discount=Discount.fixed("30.00", label="promo"),
            ),
        ],
        tax_rate=Decimal("18"),
        invoice_discount=Discount.fixed("100.00", label="early-bird"),
        currency="USD",
        notes="Payment due within 14 days. Thank you for your business!",
    )


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"invoice-generator [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo(
    fmt: str = typer.Option("text", "--format", "-f", help="text | html"),
) -> None:
    """Build a sample invoice offline and render it as text or HTML."""
    invoice = sample_invoice()
    if fmt == "text":
        print(render_text(invoice))
    elif fmt == "html":
        print(render_html(invoice))
    else:
        console.print("[red]--format must be 'text' or 'html'[/]")
        raise typer.Exit(code=1)

    totals = compute_totals(invoice)
    console.print(f"\nGrand total: [bold green]{invoice.currency} {totals.grand_total:,.2f}[/]")


if __name__ == "__main__":
    app()
