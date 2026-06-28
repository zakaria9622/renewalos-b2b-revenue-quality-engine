"""Small formatting helpers for the Streamlit Control Tower."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

SYNTHETIC_DISCLAIMER = (
    "All records shown here are synthetic. Outputs are local diagnostics and simulated "
    "scenario recommendations, not certified KPI reporting or observed business results."
)

DATA_READINESS_WARNING = (
    "Management KPI reporting is restricted unless the current trust-status model explicitly "
    "approves it. Current RenewalOS outputs are diagnostic and synthetic."
)


def format_count(value: object) -> str:
    """Format a count-like value."""

    return f"{int(_to_decimal(value)):,.0f}"


def format_money(value: object) -> str:
    """Format a synthetic currency-like scenario amount."""

    return f"${_to_decimal(value):,.2f}"


def format_percent(value: object) -> str:
    """Format a decimal ratio as a percentage string."""

    return f"{_to_decimal(value) * Decimal('100'):,.1f}%"


def status_label(value: object) -> str:
    """Convert status keys into readable labels while preserving original meaning."""

    return str(value).replace("_", " ").title()


def _to_decimal(value: object) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal("0")
