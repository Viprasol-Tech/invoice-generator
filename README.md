<p align="center">
  <img src="docs/assets/logo.png" width="120" alt="Viprasol Tech logo">
</p>

<h1 align="center">Invoice Generator</h1>

<p align="center">
  <strong>Generate invoices in Python — line items, tax, discounts, exact-cent totals, and text/HTML rendering.</strong><br>
  Pure <code>Decimal</code> money math, no template engine, no network — runs fully offline.
</p>

<p align="center">
  <em>Built and maintained by <a href="https://viprasol.com">Viprasol Tech</a> — Fintech Experts. Full-Stack Builders.</em>
</p>

<p align="center">
  <a href="https://github.com/Viprasol-Tech/invoice-generator/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Viprasol-Tech/invoice-generator/ci.yml?style=flat-square&logo=githubactions&logoColor=white&label=CI" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Viprasol-Tech/invoice-generator?style=flat-square&color=blue" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <a href="https://t.me/viprasol_help"><img src="https://img.shields.io/badge/Telegram-support-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram"></a>
  <a href="https://github.com/Viprasol-Tech/invoice-generator/stargazers"><img src="https://img.shields.io/github/stars/Viprasol-Tech/invoice-generator?style=flat-square&logo=github" alt="Stars"></a>
</p>

---

## ✨ Features

- 🧾 **Real invoice model** — parties, line items (description, qty, unit price), notes.
- 💸 **Discounts that compose** — per-line *and* invoice-level, percentage *or* fixed amount.
- 🧮 **Exact money math** — everything is `Decimal`, rounded to cents with `ROUND_HALF_UP`.
- 🧷 **One source of truth** — subtotal → discount → tax → grand total in a single `calc` module.
- 🖨️ **Two renderers** — fixed-width plain text and a self-contained, injection-safe HTML document.
- 🖥️ **CLI** — `invoice-generator demo --format html` builds and prints a sample invoice offline.
- ⚙️ **Modern tooling** — ruff, mypy (strict), pytest, GitHub Actions CI.

## 🚀 Quickstart

```bash
git clone https://github.com/Viprasol-Tech/invoice-generator.git
cd invoice-generator
python -m pip install -e ".[dev]"

# Build and print a sample invoice (no network, no config):
invoice-generator demo --format text
invoice-generator demo --format html > invoice.html
```

## 🧩 Use it in code

```python
from decimal import Decimal

from invoice_generator.calc import compute_totals
from invoice_generator.model import Discount, Invoice, LineItem, Party
from invoice_generator.render import render_text

invoice = Invoice(
    number="INV-2025-0007",
    seller=Party(name="Viprasol Tech"),
    buyer=Party(name="Acme Corp"),
    items=[
        LineItem(
            description="Backend development", quantity=Decimal("40"), unit_price=Decimal("75.00")
        ),
        LineItem(
            description="Frontend development",
            quantity=Decimal("24"),
            unit_price=Decimal("80.00"),
            discount=Discount.percent(10),
        ),
    ],
    tax_rate=Decimal("18"),
    invoice_discount=Discount.fixed("100.00"),
)

totals = compute_totals(invoice)
print(totals.grand_total)  # Decimal('5461.04')  — exact, no float drift
print(render_text(invoice))
```

## 🏗️ Architecture

```mermaid
flowchart LR
    MODEL[model.py: Invoice / LineItem / Discount] --> CALC[calc.py: Decimal totals]
    CALC --> RENDER[render.py: text / HTML]
    RENDER --> OUT[CLI / your app]
```

## 🗺️ Roadmap

- [x] Invoice model with per-line and invoice-level discounts
- [x] Exact `Decimal` subtotal / discount / tax / grand-total math
- [x] Plain-text and HTML renderers + offline CLI demo
- [ ] PDF export (via an optional renderer backend)
- [ ] Multi-currency formatting and locale-aware number display
- [ ] Recurring invoices and payment-status tracking

## 🤝 Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).

## Contact — Viprasol Tech Private Limited

- Website: [viprasol.com](https://viprasol.com)
- Email: [support@viprasol.com](mailto:support@viprasol.com)
- Telegram: [t.me/viprasol_help](https://t.me/viprasol_help) | WhatsApp: +91 96336 52112
- GitHub: [@Viprasol-Tech](https://github.com/Viprasol-Tech) | [LinkedIn](https://www.linkedin.com/in/viprasol/) | X [@viprasol](https://twitter.com/viprasol)

## License

[MIT](LICENSE) (c) 2025 Viprasol Tech Private Limited
