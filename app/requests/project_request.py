from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any


@dataclass
class CreateProjectRequest:
    name: str
    pm_name: str
    project_id: str
    bank_id: Optional[str] = None
    project_link: Optional[str] = None
    
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
        
        if errors:
            return None, errors
        
        return cls(
            name=name,
            pm_name=pm_name,
            project_id=project_id,
            bank_id=bank_id,
            project_link=project_link
        ), None


@dataclass
class UpdateProjectRequest:
    name: Optional[str] = None
    pm_name: Optional[str] = None
    project_id: Optional[str] = None
    bank_id: Optional[str] = None
    project_link: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> Tuple[Optional["UpdateProjectRequest"], Optional[List[str]]]:
        """Parse and validate update project request"""
        errors = []
        
        name = data.get("name")
        pm_name = data.get("pmName")
        project_id = data.get("projectId")
        bank_id = data.get("bankId")
        project_link = data.get("projectLink")
        
        # No validation needed for optional update
        return cls(
            name=name.strip() if name else None,
            pm_name=pm_name.strip() if pm_name else None,
            project_id=project_id.strip() if project_id else None,
            bank_id=bank_id,
            project_link=project_link.strip() if project_link else None
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
        
        # Remove duplicates based on user_id
        seen = set()
        unique_members = []

        for member in members:
            user_id = member.get("userId")

            if not user_id:
                errors.append("Each member must have user_id")
                continue

            if user_id not in seen:
                seen.add(user_id)
                unique_members.append(member)

        if errors:
            return None, errors

        return cls(members=unique_members), None