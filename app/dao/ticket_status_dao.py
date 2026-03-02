

from app.models.ticket_status import TicketStatus
from app import db
from typing import Optional, List


class TicketStatusDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[TicketStatus]:
        """Get ticket status by UUID"""
        return TicketStatus.query.filter_by(id=id).first()

    @staticmethod
    def get_by_status_id(status_id: str) -> Optional[TicketStatus]:
        """Get ticket status by status_id (string)"""
        return TicketStatus.query.filter_by(status_id=status_id).first()
    
    @staticmethod
    def get_all() -> List[TicketStatus]:
        """Get all ticket statuses"""
        return TicketStatus.query.all()
    
    # ---------- CREATE ----------
    @staticmethod
    def create(
        status_id: str,
        name: str
    ) -> TicketStatus:
        """Create new ticket status"""
        try:
            ticket_status = TicketStatus(
                status_id=status_id,
                name=name
            )
            db.session.add(ticket_status)
            db.session.commit()
            return ticket_status
        except Exception:
            db.session.rollback()
            raise

    # ---------- CREATE MULTIPLE ----------
    @staticmethod
    def create_multiple(ticket_statuses_data: List[dict]) -> List[TicketStatus]:
        """Create multiple ticket statuses
        
        Args:
            ticket_statuses_data: List of dicts with keys: status_id, name
        
        Returns:
            List of created TicketStatus objects
        """
        try:
            created_statuses = []
            for data in ticket_statuses_data:
                ticket_status = TicketStatus(
                    status_id=data['status_id'],
                    name=data['name']
                )
                db.session.add(ticket_status)
                created_statuses.append(ticket_status)
            db.session.commit()
            return created_statuses
        except Exception:
            db.session.rollback()
            raise

    # ---------- DELETE ----------
    @staticmethod
    def delete(id: str) -> bool:
        """Delete ticket status by UUID"""
        try:
            ticket_status = TicketStatusDAO.get_by_id(id)
            
            if not ticket_status:
                return False
            
            db.session.delete(ticket_status)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise


