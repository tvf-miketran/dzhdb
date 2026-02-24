from dataclasses import dataclass
from typing import Optional, List, Tuple
from decimal import Decimal


@dataclass
class CreateLogworkRequest:
    user_id: str
    log_hours: Decimal
    month: str
    year: str = '2026'
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["CreateLogworkRequest"], Optional[List[str]]]:
        """Parse and validate create logwork request"""
        errors = []
        
        # Get user_id
        user_id = data.get("userId")
        if not user_id:
            errors.append("userId is required")
        
        # Get log_hours as number
        log_hours_raw = data.get("logHour")
        if log_hours_raw is None:
            errors.append("logHour is required")
        else:
            try:
                log_hours = Decimal(str(log_hours_raw))
                if log_hours <= 0:
                    errors.append("logHour must be greater than 0")
            except (ValueError, TypeError):
                errors.append("logHour must be a valid number")
        
        # Get month
        month = data.get("month")
        if not month:
            errors.append("month is required")
        else:
            month = str(month).strip()
            try:
                month_int = int(month)
                if month_int < 1 or month_int > 12:
                    errors.append("month must be between 1 and 12")
                else:
                    # Format month with leading zero (1 -> "01", 10 -> "10")
                    month = str(month_int).zfill(2)
            except ValueError:
                errors.append("month must be a numeric string (1-12)")
        
        # Get year (optional, defaults to 2026)
        year = data.get("year", "2026")
        year = str(year).strip()
        try:
            year_int = int(year)
            if year_int < 1900 or year_int > 2100:
                errors.append("year must be between 1900 and 2100")
            else:
                year = str(year_int)
        except ValueError:
            errors.append("year must be a numeric string")
        
        if errors:
            return None, errors
        
        return cls(user_id=user_id, log_hours=log_hours, month=month, year=year), None


@dataclass
class UpdateLogworkRequest:
    log_hours: Optional[Decimal] = None
    month: Optional[str] = None
    year: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdateLogworkRequest"], Optional[List[str]]]:
        """Parse and validate update logwork request"""
        errors = []
        
        log_hours = None
        month = None
        year = None
        
        # Validation for log_hours
        log_hours_raw = data.get("logHour")
        if log_hours_raw is not None:
            try:
                log_hours = Decimal(str(log_hours_raw))
                if log_hours <= 0:
                    errors.append("logHour must be greater than 0")
            except (ValueError, TypeError):
                errors.append("logHour must be a valid number")
        
        # Validation for month
        month_raw = data.get("month")
        if month_raw is not None:
            month = str(month_raw).strip()
            try:
                month_int = int(month)
                if month_int < 1 or month_int > 12:
                    errors.append("month must be between 1 and 12")
                else:
                    # Format month with leading zero (1 -> "01", 10 -> "10")
                    month = str(month_int).zfill(2)
            except ValueError:
                errors.append("month must be a numeric string (1-12)")
        
        # Validation for year
        year_raw = data.get("year")
        if year_raw is not None:
            year = str(year_raw).strip()
            try:
                year_int = int(year)
                if year_int < 1900 or year_int > 2100:
                    errors.append("year must be between 1900 and 2100")
                else:
                    year = str(year_int)
            except ValueError:
                errors.append("year must be a numeric string")
        
        if errors:
            return None, errors
        
        return cls(log_hours=log_hours, month=month, year=year), None
