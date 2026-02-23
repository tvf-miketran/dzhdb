from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class CreateBankRequest:
    name: str
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["CreateBankRequest"], Optional[List[str]]]:
        """Parse and validate create bank request"""
        errors = []
        
        name = data.get("name", "").strip()
        
        # Validation
        if not name:
            errors.append("Bank name is required")
        
        if len(name) < 2:
            errors.append("Bank name must be at least 2 characters")
        
        if len(name) > 255:
            errors.append("Bank name must not exceed 255 characters")
        
        if errors:
            return None, errors
        
        return cls(name=name), None


@dataclass
class UpdateBankRequest:
    name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdateBankRequest"], Optional[List[str]]]:
        """Parse and validate update bank request"""
        errors = []
        
        name = data.get("name")
        
        # Validation
        if name is not None:
            name = name.strip()
            
            if not name:
                errors.append("Bank name cannot be empty")
            
            if len(name) < 2:
                errors.append("Bank name must be at least 2 characters")
            
            if len(name) > 255:
                errors.append("Bank name must not exceed 255 characters")
        
        if errors:
            return None, errors
        
        return cls(name=name), None