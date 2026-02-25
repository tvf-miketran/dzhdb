from typing import Optional, List
from app.models.role import Role
from app import db


class RoleDAO:

    @staticmethod
    def get_by_id(id: str) -> Optional[Role]:
        """Get role by UUID"""
        return Role.query.filter_by(id=id).first()

    @staticmethod
    def get_by_role_id(role_id: str) -> Optional[Role]:
        """Get role by role_id (e.g. 'DEV', 'QA')"""
        return Role.query.filter_by(role_id=role_id).first()

    @staticmethod
    def get_by_name(name: str) -> Optional[Role]:
        """Get role by name (case-insensitive)"""
        return Role.query.filter(Role.name.ilike(name)).first()

    @staticmethod
    def get_all() -> List[Role]:
        """Get all roles"""
        return Role.query.order_by(Role.name).all()

    @staticmethod
    def create(role_id: str, name: str) -> Role:
        """Create new role"""
        try:
            role = Role(role_id=role_id, name=name)
            db.session.add(role)
            db.session.commit()
            return role
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update(id: str, role_id: str = None, name: str = None) -> Optional[Role]:
        """Update role"""
        try:
            role = RoleDAO.get_by_id(id)
            if not role:
                return None
            if role_id is not None:
                role.role_id = role_id
            if name is not None:
                role.name = name
            db.session.commit()
            return role
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(id: str) -> bool:
        """Delete role by UUID"""
        try:
            role = RoleDAO.get_by_id(id)
            if not role:
                return False
            db.session.delete(role)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise