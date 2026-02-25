from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime


def parse_date_ddmmyyyy(date_str: Optional[str]) -> Tuple[Optional[datetime], Optional[str]]:
    """Parse date string in DDMMYYYY format to datetime object
    
    Args:
        date_str: Date string in format DDMMYYYY (e.g., "24022026")
    
    Returns:
        Tuple of (datetime object, error message). If successful, error is None.
    """
    if not date_str:
        return None, None
    
    date_str = date_str.strip()
    if not date_str:
        return None, None
    
    if len(date_str) != 8:
        return None, f"Date must be in DDMMYYYY format (8 digits)"
    
    if not date_str.isdigit():
        return None, f"Date must contain only digits in DDMMYYYY format"
    
    try:
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = int(date_str[4:8])
        
        # Create datetime object (set to midnight)
        dt = datetime(year=year, month=month, day=day)
        return dt, None
    except ValueError as e:
        return None, f"Invalid date: {str(e)}"


@dataclass
class CreateProjectRequest:
    name: str
    pm_name: str
    project_id: str
    bank_id: Optional[str] = None
    project_link: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["CreateProjectRequest"], Optional[List[str]]]:
        """Parse and validate create project request"""
        errors = []
        
        name = data.get("name", "").strip()
        pm_name = data.get("pmName", "").strip()
        project_id = data.get("projectId", "").strip()
        bank_id = data.get("bankId")
        project_link = data.get("projectLink", "").strip() or None
        
        # Validation
        if not name:
            errors.append("Project name is required")
        
        if not pm_name:
            errors.append("PM name is required")
        
        if not project_id:
            errors.append("Project ID is required")
        
        # Parse dates in DDMMYYYY format
        start_date, start_date_error = parse_date_ddmmyyyy(data.get("startDate"))
        if start_date_error:
            errors.append(f"Start Date: {start_date_error}")
        
        end_date, end_date_error = parse_date_ddmmyyyy(data.get("endDate"))
        if end_date_error:
            errors.append(f"End Date: {end_date_error}")
        
        if errors:
            return None, errors
        
        return cls(
            name=name,
            pm_name=pm_name,
            project_id=project_id,
            bank_id=bank_id,
            project_link=project_link,
            start_date=start_date,
            end_date=end_date
        ), None


@dataclass
class UpdateProjectRequest:
    name: Optional[str] = None
    pm_name: Optional[str] = None
    project_id: Optional[str] = None
    bank_id: Optional[str] = None
    project_link: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdateProjectRequest"], Optional[List[str]]]:
        """Parse and validate update project request"""
        errors = []
        
        name = data.get("name")
        pm_name = data.get("pmName")
        project_id = data.get("projectId")
        bank_id = data.get("bankId")
        project_link = data.get("projectLink")
        
        # Parse dates in DDMMYYYY format (if provided)
        start_date = None
        if data.get("startDate"):
            start_date, start_date_error = parse_date_ddmmyyyy(data.get("startDate"))
            if start_date_error:
                errors.append(f"Start Date: {start_date_error}")
        
        end_date = None
        if data.get("endDate"):
            end_date, end_date_error = parse_date_ddmmyyyy(data.get("endDate"))
            if end_date_error:
                errors.append(f"End Date: {end_date_error}")
        
        if errors:
            return None, errors
        
        # No validation needed for optional update
        return cls(
            name=name.strip() if name else None,
            pm_name=pm_name.strip() if pm_name else None,
            project_id=project_id.strip() if project_id else None,
            bank_id=bank_id,
            project_link=project_link.strip() if project_link else None,
            start_date=start_date,
            end_date=end_date
        ), None


@dataclass
class AddProjectMembersRequest:
    members: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["AddProjectMembersRequest"], Optional[List[str]]]:
        """Parse and validate add project members request"""
        errors = []
        
        members = data.get("members", [])

        # Validate existence
        if members is None:
            errors.append("Members list is required")
            return None, errors

        # Validate type
        if not isinstance(members, list):
            errors.append("Members must be an array")
            return None, errors
        
        if not members:
            errors.append("Members list cannot be empty")
            return None, errors
        
        # Remove duplicates based on user_id, keeping highest allocationPercent
        seen = {}  # user_id -> member with highest allocationPercent

        for member in members:
            user_id = member.get("userId")

            if not user_id:
                errors.append("Each member must have user_id")
                continue

            if user_id not in seen:
                seen[user_id] = member
            else:
                current_alloc = seen[user_id].get("allocationPercent", 0)
                new_alloc = member.get("allocationPercent", 0)
                if new_alloc > current_alloc:
                    seen[user_id] = member

        if errors:
            return None, errors

        return cls(members=list(seen.values())), None


@dataclass
class RemoveProjectMembersRequest:
    members: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["RemoveProjectMembersRequest"], Optional[List[str]]]:
        """Parse and validate remove project members request"""
        errors = []
        
        members = data.get("members", [])

        # Validate existence
        if members is None:
            errors.append("Members list is required")
            return None, errors

        # Validate type
        if not isinstance(members, list):
            errors.append("Members must be an array")
            return None, errors
        
        if not members:
            errors.append("Members list cannot be empty")
            return None, errors
        
        # Validate each member has userId
        for idx, member in enumerate(members):
            user_id = member.get("userId")
            
            if not user_id:
                errors.append(f"Member {idx + 1}: userId is required")
        
        if errors:
            return None, errors

        return cls(members=members), None