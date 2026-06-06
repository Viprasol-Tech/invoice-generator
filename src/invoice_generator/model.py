"""Invoice data model — line items, discounts, tax and party details.

The model layer is pure data: it holds the *inputs* to an invoice (who, what,
how much, which discounts and tax rate) but performs **no** money arithmetic.
All totalling lives in :mod:`invoice_generator.calc` so the rounding rules stay
in exactly one place.

Money is represented with :class:`~decimal.Decimal` everywhere. Floats are never
used for currency, which keeps cents exact.

Part of Invoice Generator by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DiscountKind(str, Enum):
    """How a discount value should be interpreted."""

    PERCENT = "percent"
    """The value is a percentage of the base, e.g. ``Decimal("10")`` == 10%."""

    FIXED = "fixed"
    """The value is an absolute money amount in the invoice currency."""


class Discount(BaseModel):
    """A discount applied either to a single line or to the whole invoice.

    Attributes:
        kind: Whether ``value`` is a percentage or a fixed money amount.
        value: The magnitude of the discount. For :attr:`DiscountKind.PERCENT`
            this is a percentage in the range ``0``-``100``; for
            :attr:`DiscountKind.FIXED` it is an absolute amount ``>= 0``.
        label: Optional human-readable reason shown on the rendered invoice.
    """

    model_config = ConfigDict(frozen=True)

    kind: DiscountKind
    value: Decimal = Field(ge=Decimal(0))
    label: str = ""

    @classmethod
    def percent(cls, value: Decimal | int | str, label: str = "") -> Discount:
        """Build a percentage discount (e.g. ``Discount.percent(10)`` == 10%)."""
        pct = Decimal(str(value))
        if not (Decimal(0) <= pct <= Decimal(100)):
            raise ValueError("percentage discount must be between 0 and 100")
        return cls(kind=DiscountKind.PERCENT, value=pct, label=label)

    @classmethod
    def fixed(cls, value: Decimal | int | str, label: str = "") -> Discount:
        """Build a fixed-amount discount in the invoice currency."""
        return cls(kind=DiscountKind.FIXED, value=Decimal(str(value)), label=label)


class LineItem(BaseModel):
    """A single billable line on an invoice.

    Attributes:
        description: Free-text description of the goods or service.
        quantity: How many units. May be fractional (e.g. ``2.5`` hours).
        unit_price: Price of one unit, before any discount or tax.
        discount: Optional per-line discount applied to this line's gross.
    """

    model_config = ConfigDict(frozen=True)

    description: str
    quantity: Decimal = Field(gt=Decimal(0))
    unit_price: Decimal = Field(ge=Decimal(0))
    discount: Discount | None = None

    @field_validator("quantity", "unit_price", mode="before")
    @classmethod
    def _coerce_decimal(cls, v: object) -> Decimal:
        """Accept ints, floats-as-strings and strings as exact Decimals."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class Party(BaseModel):
    """A billing party — the seller (``from``) or the buyer (``to``)."""

    model_config = ConfigDict(frozen=True)

    name: str
    address: str = ""
    email: str = ""


class Invoice(BaseModel):
    """A complete invoice ready to be totalled and rendered.

    Attributes:
        number: Human-facing invoice number, e.g. ``"INV-2025-001"``.
        seller: The party issuing the invoice.
        buyer: The party being billed.
        items: One or more :class:`LineItem` rows.
        tax_rate: Tax rate as a percentage (e.g. ``Decimal("18")`` == 18%).
            Applied to the post-discount subtotal. ``0`` means tax-exempt.
        invoice_discount: Optional discount applied to the whole invoice
            *after* per-line discounts but *before* tax.
        currency: ISO-4217-ish currency code used purely for display.
        notes: Free-text footer shown on the rendered invoice.
    """

    model_config = ConfigDict(frozen=True)

    number: str
    seller: Party
    buyer: Party
    items: list[LineItem] = Field(min_length=1)
    tax_rate: Decimal = Field(default=Decimal(0), ge=Decimal(0))
    invoice_discount: Discount | None = None
    currency: str = "USD"
    notes: str = ""

    @field_validator("tax_rate", mode="before")
    @classmethod
    def _coerce_tax(cls, v: object) -> Decimal:
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))
