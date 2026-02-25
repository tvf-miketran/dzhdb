from typing import Optional, List, Dict, Any, Tuple
from app.dao.role_dao import RoleDAO
from app.models.role import Role


class RoleService:
    
    @staticmethod
    def get_all() -> List[Role]:
        """Get all roles"""
        return RoleDAO.get_all()