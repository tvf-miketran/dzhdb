from dataclasses import dataclass
from typing import Optional, List, Tuple
import re


@dataclass
class CreateEmployeeRequest:
    vn_full_name: str
    en_full_name: str
    email: str
    description: str
    password: str = None
    authorize_role: str = "MEMBER"
    employee_id: str = "N/A"
    status: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["CreateEmployeeRequest"], Optional[List[str]]]:
        """Parse and validate create employee request"""
        errors = []
        
        vn_full_name = data.get("vnFullName", "").strip()
        en_full_name = data.get("enFullName", "").strip()
        email = data.get("email", "").strip()
        description = data.get("description", "").strip()
        
        # Auto-generate fields
        employee_id = data.get("employeeId", "").strip() or "N/A"
        password = data.get("password", email)
        authorize_role = data.get("authorizeRole", "MEMBER").upper()
        status = data.get("status", True)
        
        # Validation - All fields required except EE
        if not vn_full_name:
            errors.append("Vietnamese name is required")
        
        if not en_full_name:
            errors.append("English name is required")
        
        if not email:
            errors.append("Email is required")
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            errors.append("Invalid email format")
        
        if not description:
            errors.append("Description is required")
        
        if not password:
            errors.append("Password is required")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters")
        
        if authorize_role not in ["MEMBER", "MANAGER"]:
            errors.append("Authorize role must be MEMBER or MANAGER")
        
        if errors:
            return None, errors
        
        return cls(
            vn_full_name=vn_full_name,
            en_full_name=en_full_name,
            email=email,
            employee_id=employee_id,
            description=description,
            password=password,
            authorize_role=authorize_role,
            status=status
        ), None


@dataclass
class UpdateEmployeeRequest:
    vn_full_name: Optional[str] = None
    en_full_name: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    employee_id: Optional[str] = None
    authorize_role: Optional[str] = None
    status: Optional[bool] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdateEmployeeRequest"], Optional[List[str]]]:
        """Parse and validate update employee request"""
        errors = []
        
        vn_full_name = data.get("vnFullName")
        en_full_name = data.get("enFullName")
        email = data.get("email")
        description = data.get("description")
        employee_id = data.get("employeeId")
        authorize_role = data.get("authorizeRole")
        status = data.get("status")
        
        # Validation
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            errors.append("Invalid email format")
        
        if authorize_role and authorize_role.upper() not in ["MEMBER", "MANAGER"]:
            errors.append("Authorize role must be MEMBER or MANAGER")
        
        if errors:
            return None, errors
        
        return cls(
            vn_full_name=vn_full_name.strip() if vn_full_name else None,
            en_full_name=en_full_name.strip() if en_full_name else None,
            email=email.strip() if email else None,
            description=description.strip() if description else None,
            employee_id=employee_id.strip() if employee_id else None,
            authorize_role=authorize_role.upper() if authorize_role else None,
            status=status
        ), None


@dataclass
class DeleteEmployeeRequest:
    confirm: bool
    reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["DeleteEmployeeRequest"], Optional[List[str]]]:
        """Parse and validate delete employee request"""
        errors = []

        if not isinstance(data, dict):
            return None, ["Invalid request body"]

        confirm = data.get("confirm")
        reason = data.get("reason")

        if not isinstance(confirm, bool):
            errors.append("confirm must be a boolean")
        elif not confirm:
            errors.append("confirm must be true to delete employee")

        if reason is not None and not isinstance(reason, str):
            errors.append("reason must be a string")

        if errors:
            return None, errors

        return cls(
            confirm=confirm,
            reason=reason.strip() if isinstance(reason, str) else None
        ), None