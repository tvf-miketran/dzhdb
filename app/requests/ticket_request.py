from dataclasses import dataclass
from typing import Optional, List, Tuple
import re
from datetime import datetime, timedelta
import calendar


def calculate_weeks_in_month(month: int, year: int = None) -> list:
    """Calculate weeks in a month
    
    Args:
        month: Month number (1-12)
        year: Year (default: current year)
    
    Returns:
        List of week strings like "1 (01/01/2026-04/01/2026)"
    """
    if year is None:
        year = datetime.now().year
    
    # Get the first day of the month
    first_day = datetime(year, month, 1)
    
    # Get the last day of the month
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    weeks = []
    week_num = 1
    
    # Week 1: from day 1 to the first Sunday
    # weekday(): Monday=0, ..., Saturday=5, Sunday=6
    first_sunday = first_day + timedelta(days=(6 - first_day.weekday()))
    
    # Don't go past last day of month
    if first_sunday > last_day:
        first_sunday = last_day
    
    week_str = f"{week_num} ({first_day.strftime('%d/%m/%Y')}-{first_sunday.strftime('%d/%m/%Y')})"
    weeks.append(week_str)
    
    # Subsequent weeks: start from next Monday
    week_start = first_sunday + timedelta(days=1)
    week_num = 2
    
    while week_start <= last_day:
        # Week ends on Sunday
        week_end = week_start + timedelta(days=6)
        
        # Don't go past last day of month
        if week_end > last_day:
            week_end = last_day
        
        # Format the week string
        week_str = f"{week_num} ({week_start.strftime('%d/%m/%Y')}-{week_end.strftime('%d/%m/%Y')})"
        weeks.append(week_str)
        
        # Move to next Monday
        week_start = week_end + timedelta(days=1)
        week_num += 1
    
    return weeks


def validate_week_in_month(week: Optional[int], month: Optional[int]) -> Optional[str]:
    """Validate that the week exists in the given month
    
    Args:
        week: Week number (1-based)
        month: Month number (1-12)
    
    Returns:
        Error message if invalid, None if valid
    """
    # If no week or month provided, skip validation
    if week is None or month is None:
        return None
    
    # Calculate valid weeks for the month
    valid_weeks = calculate_weeks_in_month(month)
    
    # Check if week number is valid (1 to number of weeks in month)
    if week < 1 or week > len(valid_weeks):
        available_weeks = ", ".join([f"week {i+1}" for i in range(len(valid_weeks))])
        return f"Week {week} is invalid for month {month}. Available: {available_weeks}"
    
    return None


def parse_week_string(week_str: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    """Parse week string like "1 (01/01/2026-04/01/2026)" to extract week number
    
    Args:
        week_str: Week string in format "WEEK_NUMBER (DD/MM/YYYY-DD/MM/YYYY)"
    
    Returns:
        Tuple of (week_number, error_message)
    """
    if not week_str:
        return None, None
    
    week_str = week_str.strip()
    if not week_str:
        return None, None
    
    # Pattern: "1 (01/01/2026-04/01/2026)" or just "1"
    pattern = r'^(\d+)\s*(\([^)]*\))?$'
    match = re.match(pattern, week_str)
    
    if match:
        week_num = int(match.group(1))
        return week_num, None
    
    try:
        week_num = int(week_str)
        return week_num, None
    except ValueError:
        return None, f"Invalid week format: '{week_str}'. Expected format: '1 (01/01/2026-04/01/2026)'"


def parse_role_ids(data: dict) -> Optional[List[str]]:
    """Parse and deduplicate role_ids from request data
    
    Args:
        data: Request dictionary
    
    Returns:
        List of unique role IDs (deduplicated), or None if not provided
    """
    # Handle role_ids as array (can also accept single roleId for backward compatibility)
    role_ids = data.get("roleIds")
    if role_ids is None:
        # Backward compatibility: also check for single roleId
        role_id_single = data.get("roleId")
        if role_id_single:
            role_ids = [role_id_single] if isinstance(role_id_single, str) else role_id_single
    
    # Validate and remove duplicate role IDs while preserving order
    if role_ids and isinstance(role_ids, list):
        seen = set()
        unique_role_ids = []
        for rid in role_ids:
            if rid and rid not in seen:
                seen.add(rid)
                unique_role_ids.append(rid)
        role_ids = unique_role_ids if unique_role_ids else None
    
    return role_ids


@dataclass
class CreateTicketRequest:
    ticket_id: str
    project_id: str
    ticket_link: Optional[str] = None
    role_ids: Optional[List[str]] = None
    employee_id: Optional[str] = None
    ticket_type_id: Optional[str] = None
    ticket_status_id: Optional[str] = None
    week: Optional[int] = None
    month: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["CreateTicketRequest"], Optional[List[str]]]:
        """Parse and validate create ticket request"""
        errors = []
        
        # Handle None values properly - convert to string first before stripping
        ticket_id_raw = data.get("ticketId")
        ticket_id = str(ticket_id_raw).strip() if ticket_id_raw is not None else ""
        
        project_id_raw = data.get("projectId")
        project_id = str(project_id_raw).strip() if project_id_raw is not None else ""
        
        ticket_link_raw = data.get("ticketLink")
        ticket_link = str(ticket_link_raw).strip() if ticket_link_raw is not None else None
        if ticket_link == "":
            ticket_link = None
        
        # Parse and deduplicate role IDs
        role_ids = parse_role_ids(data)
        
        employee_id = data.get("employeeId")
        ticket_type_id = data.get("ticketTypeId")
        ticket_status_id = data.get("ticketStatusId")
        week_str = data.get("week")
        month = data.get("month")
        
        # Validation
        if not ticket_id:
            errors.append("Ticket ID is required")
        
        if not project_id:
            errors.append("Project ID is required")
        
        # Parse week string (format: "1 (01/01/2026-04/01/2026)")
        week = None
        if week_str:
            week, week_error = parse_week_string(week_str)
            if week_error:
                errors.append(week_error)
        
        # Parse month if provided
        if month:
            try:
                month = int(month)
                if month < 1 or month > 12:
                    errors.append("Month must be between 1 and 12")
                    month = None
            except ValueError:
                errors.append("Invalid month format")
                month = None
        
        # Validate week exists in the month
        if week and month:
            week_error = validate_week_in_month(week, month)
            if week_error:
                errors.append(week_error)
        
        if errors:
            return None, errors
        
        return cls(
            ticket_id=ticket_id,
            project_id=project_id,
            ticket_link=ticket_link,
            role_ids=role_ids,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month
        ), None


@dataclass
class UpdateTicketRequest:
    ticket_id: Optional[str] = None
    ticket_link: Optional[str] = None
    project_id: Optional[str] = None
    role_ids: Optional[List[str]] = None
    employee_id: Optional[str] = None
    ticket_type_id: Optional[str] = None
    ticket_status_id: Optional[str] = None
    week: Optional[int] = None
    month: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdateTicketRequest"], Optional[List[str]]]:
        """Parse and validate update ticket request"""
        errors = []
        
        # Handle all fields properly - handle None values and different types
        ticket_id_raw = data.get("ticketId")
        ticket_id = str(ticket_id_raw).strip() if ticket_id_raw is not None else None
        if ticket_id == "":
            ticket_id = None
            
        ticket_link_raw = data.get("ticketLink")
        ticket_link = str(ticket_link_raw).strip() if ticket_link_raw is not None else None
        if ticket_link == "":
            ticket_link = None
            
        project_id_raw = data.get("projectId")
        project_id = str(project_id_raw).strip() if project_id_raw is not None else None
        if project_id == "":
            project_id = None
        
        # Parse and deduplicate role IDs
        role_ids = parse_role_ids(data)
        
        employee_id = data.get("employeeId")
        ticket_type_id = data.get("ticketTypeId")
        ticket_status_id = data.get("ticketStatusId")
        week_str = data.get("week")
        month = data.get("month")
        
        # Parse week string (format: "1 (01/01/2026-04/01/2026)")
        week = None
        if week_str:
            week, week_error = parse_week_string(week_str)
            if week_error:
                errors.append(week_error)
        
        # Parse month if provided
        if month:
            try:
                month = int(month)
                if month < 1 or month > 12:
                    errors.append("Month must be between 1 and 12")
                    month = None
            except ValueError:
                errors.append("Invalid month format")
                month = None
        
        # Validate week exists in the month
        if week and month:
            week_error = validate_week_in_month(week, month)
            if week_error:
                errors.append(week_error)
        
        if errors:
            return None, errors
        
        return cls(
            ticket_id=ticket_id,
            ticket_link=ticket_link,
            project_id=project_id,
            role_ids=role_ids,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month
        ), None

