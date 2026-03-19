def _round_floats(value, ndigits: int = 2):
    """Recursively round float values for API responses."""
    if isinstance(value, float):
        return round(value, ndigits)
    if isinstance(value, list):
        return [_round_floats(item, ndigits) for item in value]
    if isinstance(value, dict):
        return {key: _round_floats(val, ndigits) for key, val in value.items()}
    return value