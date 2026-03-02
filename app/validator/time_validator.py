# Validate start_date and end_date (compare with existing values if not provided)
# Handle DDMMYYYY format and datetime objects
from datetime import datetime

def parse_date(date_val):
    """Parse date from string (DDMMYYYY or ISO) or datetime object"""
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, str):
        try:
            # Try DDMMYYYY format first
            if len(date_val) == 8 and date_val.isdigit():
                day = int(date_val[0:2])
                month = int(date_val[2:4])
                year = int(date_val[4:8])
                return datetime(year, month, day)
            else:
                # Try ISO format
                return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        except (ValueError, IndexError):
            return None
    return None