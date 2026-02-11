from typing import Optional, List, Dict, Any, Tuple
from app.dao.bank_dao import BankDAO
from app.models.bank import Bank


class BankService:
    
    @staticmethod
    def get_all() -> List[Bank]:
        """Get all banks"""
        return BankDAO.get_all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get filtered and sorted banks with pagination"""
        
        # Validate sort_by field
        valid_sort_fields = ["created_at", "name"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"
        
        pagination = BankDAO.get_all_filtered_sorted(
            page=page,
            per_page=per_page,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "items": [BankService._to_dict(bank) for bank in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "filters": {
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Bank]:
        """Get bank by UUID"""
        return BankDAO.get_by_id(id)
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Bank]:
        """Get bank by name"""
        return BankDAO.get_by_name(name)
    
    @staticmethod
    def _to_dict(bank: Bank, include_projects: bool = False) -> Dict[str, Any]:
        """Convert bank to dictionary"""
        result = {
            "id": str(bank.id),
            "name": bank.name,
            "createdAt": bank.created_at.isoformat() if bank.created_at else None
        }
        
        # Add projects information if requested
        if include_projects:
            result["projects"] = [
                {
                    "id": str(project.id),
                    "projectId": project.project_id,
                    "name": project.name,
                    "pmName": project.pm_name,
                    "projectLink": project.project_link,
                    "createdAt": project.created_at.isoformat() if project.created_at else None
                }
                for project in bank.projects
            ]
            result["projectCount"] = len(bank.projects)
        
        return result
        
    @staticmethod
    def create(name: str) -> Tuple[Optional[Bank], Optional[List[str]]]:
        """Create new bank with validation"""
        errors = []
        
        # Check if bank name already exists
        if BankDAO.get_by_name(name):
            errors.append(f"Bank name '{name}' already exists")
        
        if errors:
            return None, errors
        
        try:
            bank = BankDAO.create(name=name)
            return bank, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def update(id: str, name: str = None) -> Tuple[Optional[Bank], Optional[List[str]]]:
        """Update bank"""
        bank = BankDAO.get_by_id(id)
        
        if not bank:
            return None, ["Bank not found"]
        
        errors = []
        
        # Check if new name already exists (for different bank)
        if name and name != bank.name:
            existing = BankDAO.get_by_name(name)
            if existing:
                errors.append(f"Bank name '{name}' already exists")
        
        if errors:
            return None, errors
        
        try:
            updated = BankDAO.update(id=id, name=name)
            return updated, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def delete(id: str) -> Tuple[bool, Optional[str]]:
        """Delete bank"""
        bank = BankDAO.get_by_id(id)
        
        if not bank:
            return False, "Bank not found"
        
        try:
            success = BankDAO.delete(id)
            return success, None
        except Exception as e:
            return False, str(e)