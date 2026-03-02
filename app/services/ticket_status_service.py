

from typing import Optional, List, Dict, Any, Tuple
from app.dao.ticket_status_dao import TicketStatusDAO


class TicketStatusService:

    @staticmethod
    def get_all() -> List[Any]:
        """Get all ticket statuses"""
        return TicketStatusDAO.get_all()
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Any]:
        """Get ticket status by UUID"""
        return TicketStatusDAO.get_by_id(id)
    
    @staticmethod
    def create(
        status_id: str,
        name: str
    ) -> Tuple[Optional[Any], Optional[List[str]]]:
        """Create new ticket status with validation"""
        errors = []
        
        # Check if status_id already exists
        if TicketStatusDAO.get_by_status_id(status_id):
            errors.append(f"Ticket status ID '{status_id}' already exists")
        
        if errors:
            return None, errors
        
        try:
            ticket_status = TicketStatusDAO.create(
                status_id=status_id,
                name=name
            )
            return ticket_status, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def create_multiple(
        ticket_statuses_data: List[Dict[str, Any]]
    ) -> Tuple[Optional[List[Any]], Optional[List[str]]]:
        """Create multiple ticket statuses
        
        Args:
            ticket_statuses_data: List of dicts with keys: statusId, name
        
        Returns:
            Tuple of (created list, errors list)
        """
        errors = []
        validated_data = []

        # Validate each ticket status
        for idx, item in enumerate(ticket_statuses_data):
            status_id = item.get('statusId', '').strip()
            name = item.get('name', '').strip()
            
            if not status_id:
                errors.append(f"Item {idx + 1}: statusId is required")
                continue
            
            if not name:
                errors.append(f"Item {idx + 1}: name is required")
                continue
            
            validated_data.append({
                'status_id': status_id,
                'name': name
            })
        
        if errors:
            return None, errors
        
        try:
            for data in validated_data:
                # Check if status_id already exists
                if TicketStatusDAO.get_by_status_id(data['status_id']):
                    raise ValueError(f"Ticket status ID '{data['status_id']}' already exists")
            created_statuses = TicketStatusDAO.create_multiple(validated_data)
            
            # Convert to response format
            result = [
                {
                    "id": str(s.id),
                    "statusId": s.status_id,
                    "name": s.name
                }
                for s in created_statuses
            ]
            
            return result, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def delete(id: str) -> Tuple[bool, Optional[List[str]]]:
        """Delete ticket status by UUID"""
        try:
            deleted = TicketStatusDAO.delete(id)
            if not deleted:
                return False, ["Ticket status not found"]
            return True, None
        except Exception as e:
            return False, [str(e)]
    
    @staticmethod
    def _to_dict(ticket_status: Any) -> Dict[str, Any]:
        """Convert ticket status to dictionary"""
        return {
            "id": str(ticket_status.id),
            "statusId": ticket_status.status_id,
            "name": ticket_status.name
        }


