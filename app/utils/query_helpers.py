from typing import Optional, List, Any, Union


def parse_list_param(value: Any) -> Optional[List[str]]:
    """Parse query parameter that can be comma-separated string, array, or single value
    
    Args:
        value: Query parameter value (can be string, list, or None)
    
    Returns:
        List of strings or None if value is empty/invalid
    
    Examples:
        "uuid1,uuid2,uuid3" -> ["uuid1", "uuid2", "uuid3"]
        "uuid1" -> ["uuid1"]
        ["uuid1", "uuid2"] -> ["uuid1", "uuid2"]
        None -> None
    """
    if value is None:
        return None
    if isinstance(value, list):
        # Filter out empty strings
        result = [v.strip() for v in value if v and v.strip()]
        return result if result else None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        if "," in value:
            result = [v.strip() for v in value.split(",") if v and v.strip()]
            return result if result else None
        return [value]
    return None


def parse_int_list_param(value: Any) -> Optional[List[int]]:
    """Parse query parameter that can be comma-separated integers
    
    Args:
        value: Query parameter value (can be string, list, or None)
    
    Returns:
        List of integers or None if value is empty/invalid
    
    Examples:
        "1,2,3" -> [1, 2, 3]
        "1" -> [1]
        ["1", "2"] -> [1, 2]
        None -> None
    """
    if value is None:
        return None
    if isinstance(value, list):
        result = []
        for v in value:
            if v:
                try:
                    result.append(int(v))
                except (ValueError, TypeError):
                    pass
        return result if result else None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        if "," in value:
            result = []
            for v in value.split(","):
                try:
                    result.append(int(v.strip()))
                except (ValueError, TypeError):
                    pass
            return result if result else None
        try:
            return [int(value)]
        except (ValueError, TypeError):
            pass
    return None


def parse_month_list_param(value: Any) -> Optional[List[str]]:
    """Parse a comma-separated month string into zero-padded month strings.

    Invalid or out-of-range values are silently discarded.

    Args:
        value: Query parameter value (can be string, list, or None)

    Returns:
        List of zero-padded month strings, or None if empty/invalid

    Examples:
        "3,4,2,1"  -> ["03", "04", "02", "01"]
        "12"       -> ["12"]
        None       -> None
    """
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.split(",")
    elif isinstance(value, list):
        parts = value
    else:
        return None

    result = []
    for part in parts:
        try:
            month_int = int(str(part).strip())
            if 1 <= month_int <= 12:
                result.append(str(month_int).zfill(2))
        except (ValueError, TypeError):
            pass
    return result if result else None

