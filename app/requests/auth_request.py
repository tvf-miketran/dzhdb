from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class LoginRequest:
    email: str
    password: str
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["LoginRequest"], Optional[List[str]]]:
        """Parse and validate login request data"""
        errors = []
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email:
            errors.append("Email is required")
        elif "@" not in email:
            errors.append("Invalid email format")
            
        if not password:
            errors.append("Password is required")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters")
        
        if errors:
            return None, errors
        
        return cls(email=email, password=password), None


@dataclass
class UpdatePasswordRequest:
    old_password: str
    new_password: str
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdatePasswordRequest"], Optional[List[str]]]:
        """Parse and validate update password request data"""
        errors = []
        
        old_password = data.get("oldPassword", "")
        new_password = data.get("newPassword", "")
        
        if not old_password:
            errors.append("Old password is required")
            
        if not new_password:
            errors.append("New password is required")
        elif len(new_password) < 6:
            errors.append("New password must be at least 6 characters")
        
        if old_password and new_password and old_password == new_password:
            errors.append("New password must be different from old password")
        
        if errors:
            return None, errors
        
        return cls(old_password=old_password, new_password=new_password), None