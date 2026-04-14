from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any, Optional


def _normalize_numeric_text(value: str) -> str:
    """Normalize a numeric string so Decimal can parse it.

    Supports inputs like:
    - "1,35" -> "1.35"
    - "1 234,56" -> "1234.56"
    - "1,234.56" -> "1234.56"
    - "1.234,56" -> "1234.56"
    """
    text = str(value).strip().replace(" ", "")
    if not text:
        return text

    if "," in text and "." in text:
        # If the last comma appears after the last dot, treat comma as decimal separator.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")

    return text


def parse_decimal_value(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """Parse a value into Decimal, accepting comma-decimal string input."""
    if value is None:
        return default

    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, (int, float)):
        if isinstance(value, float) and not isfinite(value):
            return default
        parsed = Decimal(str(value))
    else:
        text = _normalize_numeric_text(value)
        if not text:
            return default
        try:
            parsed = Decimal(text)
        except (InvalidOperation, ValueError, TypeError):
            return default

    if parsed.is_nan() or parsed.is_infinite():
        return default

    return parsed


def parse_float_value(value: Any, default: float = 0.0) -> float:
    """Parse a value into float, accepting comma-decimal string input."""
    parsed = parse_decimal_value(value, None)
    if parsed is None:
        return default

    try:
        result = float(parsed)
    except (TypeError, ValueError, OverflowError):
        return default

    return result if isfinite(result) else default


def normalize_numeric_string(value: Any) -> Optional[str]:
    """Return a normalized numeric string, or None if the value is invalid."""
    parsed = parse_decimal_value(value, None)
    return str(parsed) if parsed is not None else None