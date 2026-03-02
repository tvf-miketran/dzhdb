
from app.models.ticket_type import TicketType
from app import db
from typing import Optional, List


class TicketTypeDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[TicketType]:
        """Get ticket type by UUID"""
        return TicketType.query.filter_by(id=id).first()

    @staticmethod
    def get_by_type_id(type_id: str) -> Optional[TicketType]:
        """Get ticket type by type_id (string)"""
        return TicketType.query.filter_by(type_id=type_id).first()
    
    @staticmethod
    def get_all() -> List[TicketType]:
        """Get all ticket types"""
        return TicketType.query.all()
    
    # ---------- CREATE ----------
    @staticmethod
    def create(
        type_id: str,
        name: str
    ) -> TicketType:
        """Create new ticket type"""
        try:
            ticket_type = TicketType(
                type_id=type_id,
                name=name
            )
            db.session.add(ticket_type)
            db.session.commit()
            return ticket_type
        except Exception:
            db.session.rollback()
            raise

    # ---------- CREATE MULTIPLE ----------
    @staticmethod
    def create_multiple(ticket_types_data: List[dict]) -> List[TicketType]:
        """Create multiple ticket types
        
        Args:
            ticket_types_data: List of dicts with keys: type_id, name
        
        Returns:
            List of created TicketType objects
        """
        try:
            created_types = []
            for data in ticket_types_data:
                ticket_type = TicketType(
                    type_id=data['type_id'],
                    name=data['name']
                )
                db.session.add(ticket_type)
                created_types.append(ticket_type)
            db.session.commit()
            return created_types
        except Exception:
            db.session.rollback()
            raise

    # ---------- DELETE ----------
    @staticmethod
    def delete(id: str) -> bool:
        """Delete ticket type by UUID"""
        try:
            ticket_type = TicketTypeDAO.get_by_id(id)
            
            if not ticket_type:
                return False
            
            db.session.delete(ticket_type)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

