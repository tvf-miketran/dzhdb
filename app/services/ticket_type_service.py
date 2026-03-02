

from typing import Optional, List, Dict, Any, Tuple
from app.dao.ticket_type_dao import TicketTypeDAO


class TicketTypeService:

    @staticmethod
    def get_all() -> List[Any]:
        """Get all ticket types"""
        return TicketTypeDAO.get_all()
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Any]:
        """Get ticket type by UUID"""
        return TicketTypeDAO.get_by_id(id)
    
    @staticmethod
    def create(
        type_id: str,
        name: str
    ) -> Tuple[Optional[Any], Optional[List[str]]]:
        """Create new ticket type with validation"""
        errors = []
        
        # Check if type_id already exists
        if TicketTypeDAO.get_by_type_id(type_id):
            errors.append(f"Ticket type ID '{type_id}' already exists")
        
        if errors:
            return None, errors
        
        try:
            ticket_type = TicketTypeDAO.create(
                type_id=type_id,
                name=name
            )
            return ticket_type, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def create_multiple(
        ticket_types_data: List[Dict[str, Any]]
    ) -> Tuple[Optional[List[Any]], Optional[List[str]]]:
        """Create multiple ticket types
        
        Args:
            ticket_types_data: List of dicts with keys: typeId, name
        
        Returns:
            Tuple of (created list, errors list)
        """
        errors = []
        validated_data = []

        # Validate each ticket type
        for idx, item in enumerate(ticket_types_data):
            type_id = item.get('typeId', '').strip()
            name = item.get('name', '').strip()
            
            if not type_id:
                errors.append(f"Item {idx + 1}: typeId is required")
                continue
            
            if not name:
                errors.append(f"Item {idx + 1}: name is required")
                continue
            
            validated_data.append({
                'type_id': type_id,
                'name': name
            })
        
        if errors:
            return None, errors
        
        try:
            for data in validated_data:
                # Check if type_id already exists
                if TicketTypeDAO.get_by_type_id(data['type_id']):
                    raise ValueError(f"Ticket type ID '{data['type_id']}' already exists")
            created_types = TicketTypeDAO.create_multiple(validated_data)
            
            # Convert to response format
            result = [
                {
                    "id": str(t.id),
                    "typeId": t.type_id,
                    "name": t.name
                }
                for t in created_types
            ]
            
            return result, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def delete(id: str) -> Tuple[bool, Optional[List[str]]]:
        """Delete ticket type by UUID"""
        try:
            deleted = TicketTypeDAO.delete(id)
            if not deleted:
                return False, ["Ticket type not found"]
            return True, None
        except Exception as e:
            return False, [str(e)]
    
    @staticmethod
    def _to_dict(ticket_type: Any) -> Dict[str, Any]:
        """Convert ticket type to dictionary"""
        return {
            "id": str(ticket_type.id),
            "typeId": ticket_type.type_id,
            "name": ticket_type.name
        }


