
from typing import Optional, List, Dict, Any, Tuple
from app.dao.ticket_dao import TicketDAO
from app.dao.project_dao import ProjectDAO
from app.dao.employee_dao import EmployeeDAO
from app.dao.role_dao import RoleDAO
from app.models.ticket import Ticket


class TicketService:

    @staticmethod
    def _validate_foreign_keys(
        project_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        role_ids: Optional[List[str]] = None,
        ticket_type_id: Optional[str] = None,
        ticket_status_id: Optional[str] = None
    ) -> List[str]:
        """Validate that all foreign key references exist
        
        Returns:
            List of error messages (empty if all valid)
        """
        errors = []
        
        # Validate project exists
        if project_id:
            project = ProjectDAO.get_by_id(project_id)
            if not project:
                errors.append(f"Project with ID '{project_id}' not found")
        
        # Validate employee exists (if provided)
        if employee_id:
            employee = EmployeeDAO.get_by_id(employee_id)
            if not employee:
                errors.append(f"Employee with ID '{employee_id}' not found")
        
        # Validate roles exist (if provided, can be array)
        if role_ids:
            if isinstance(role_ids, list):
                for role_id in role_ids:
                    role = RoleDAO.get_by_id(role_id)
                    if not role:
                        errors.append(f"Role with ID '{role_id}' not found")
            else:
                # Single role_id (backward compatibility)
                role = RoleDAO.get_by_id(role_ids)
                if not role:
                    errors.append(f"Role with ID '{role_ids}' not found")
        
        # Validate ticket_type exists (if provided)
        if ticket_type_id:
            from app.models.ticket_type import TicketType
            ticket_type = TicketType.query.filter_by(id=ticket_type_id).first()
            if not ticket_type:
                errors.append(f"TicketType with ID '{ticket_type_id}' not found")
        
        # Validate ticket_status exists (if provided)
        if ticket_status_id:
            from app.models.ticket_status import TicketStatus
            ticket_status = TicketStatus.query.filter_by(id=ticket_status_id).first()
            if not ticket_status:
                errors.append(f"TicketStatus with ID '{ticket_status_id}' not found")
        
        return errors

    @staticmethod
    def get_all() -> List[Ticket]:
        """Get all tickets"""
        return TicketDAO.get_all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        project_id: Optional[List[str]] = None,
        employee_id: Optional[List[str]] = None,
        ticket_type_id: Optional[List[str]] = None,
        ticket_status_id: Optional[List[str]] = None,
        week: Optional[List[int]] = None,
        month: Optional[List[int]] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get filtered and sorted tickets with pagination
        
        Args:
            project_id: List of project UUIDs or single project UUID (can be comma-separated string or list)
            employee_id: List of employee UUIDs or single employee UUID
            ticket_type_id: List of ticket type UUIDs or single ticket type UUID
            ticket_status_id: List of ticket status UUIDs or single ticket status UUID
            week: List of week numbers or single week number
            month: List of month numbers or single month number
        """
        
        # Validate sort_by field
        valid_sort_fields = ["created_at", "updated_at", "ticket_id"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"
        
        pagination = TicketDAO.get_all_filtered_sorted(
            page=page,
            per_page=per_page,
            project_id=project_id,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "items": [TicketService._to_dict(ticket) for ticket in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "filters": {
                "project_id": project_id,
                "employee_id": employee_id,
                "ticket_type_id": ticket_type_id,
                "ticket_status_id": ticket_status_id,
                "week": week,
                "month": month,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Ticket]:
        """Get ticket by UUID"""
        return TicketDAO.get_by_id(id)
    
    @staticmethod
    def get_by_ticket_id(ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ticket_id (string)"""
        return TicketDAO.get_by_ticket_id(ticket_id)
    
    @staticmethod
    def get_by_project_id(project_id: str) -> List[Ticket]:
        """Get all tickets for a project"""
        return TicketDAO.get_by_project_id(project_id)
          
    @staticmethod
    def create(
        ticket_id: str,
        project_id: str,
        ticket_link: Optional[str] = None,
        role_ids: Optional[List[str]] = None,
        employee_id: Optional[str] = None,
        ticket_type_id: Optional[str] = None,
        ticket_status_id: Optional[str] = None,
        week: Optional[int] = None,
        month: Optional[int] = None
    ) -> Tuple[Optional[Ticket], Optional[List[str]], Optional[str]]:
        """Create new ticket with validation. If ticket_id exists, update it instead.
        
        Returns:
            Tuple of (ticket, errors, message). Message indicates if ticket was updated.
        """
        errors = []
        message = None
        
        # Check if ticket_id already exists - if so, update instead
        # Note: This behavior might need adjustment since ticket_ids are no longer unique
        # For now, we allow duplicate ticket_ids, so we don't check for existing
        # existing_ticket = TicketDAO.get_by_ticket_id(ticket_id)
        
        # Validate foreign keys
        fk_errors = TicketService._validate_foreign_keys(
            project_id=project_id,
            employee_id=employee_id,
            role_ids=role_ids,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id
        )
        errors.extend(fk_errors)
        
        if errors:
            return None, errors, None
        
        try:
            ticket = TicketDAO.create(
                ticket_id=ticket_id,
                project_id=project_id,
                ticket_link=ticket_link,
                role_ids=role_ids,
                employee_id=employee_id,
                ticket_type_id=ticket_type_id,
                ticket_status_id=ticket_status_id,
                week=week,
                month=month
            )
            return ticket, None, message
        except Exception as e:
            return None, [str(e)], None
    
    @staticmethod
    def update(
        id: str,
        ticket_id: Optional[str] = None,
        ticket_link: Optional[str] = None,
        project_id: Optional[str] = None,
        role_ids: Optional[List[str]] = None,
        employee_id: Optional[str] = None,
        ticket_type_id: Optional[str] = None,
        ticket_status_id: Optional[str] = None,
        week: Optional[int] = None,
        month: Optional[int] = None
    ) -> Tuple[Optional[Ticket], Optional[List[str]]]:
        """Update ticket by UUID or ticket_id"""
        # Try to get by UUID first, then by ticket_id
        ticket = TicketDAO.get_by_id(id)
        if not ticket:
            ticket = TicketDAO.get_by_ticket_id(id)
        
        if not ticket:
            return None, ["Ticket not found"]
        
        errors = []
        
        # Validate foreign keys (only if provided)
        fk_errors = TicketService._validate_foreign_keys(
            project_id=project_id,
            employee_id=employee_id,
            role_ids=role_ids,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id
        )
        errors.extend(fk_errors)
        
        if errors:
            return None, errors
        
        try:
            updated = TicketDAO.update(
                id=str(ticket.id),
                ticket_id=ticket_id,
                ticket_link=ticket_link,
                project_id=project_id,
                role_ids=role_ids,
                employee_id=employee_id,
                ticket_type_id=ticket_type_id,
                ticket_status_id=ticket_status_id,
                week=week,
                month=month
            )
            return updated, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def delete(id: str) -> Tuple[bool, Optional[List[str]]]:
        """Delete ticket by UUID or ticket_id
        
        Returns:
            Tuple of (success, errors)
        """
        # Try to get by UUID first, then by ticket_id
        ticket = TicketDAO.get_by_id(id)
        if not ticket:
            ticket = TicketDAO.get_by_ticket_id(id)
        
        if not ticket:
            return False, ["Ticket not found"]
        
        try:
            deleted = TicketDAO.delete(str(ticket.id))
            return deleted, None
        except Exception as e:
            return False, [str(e)]
    
    @staticmethod
    def _to_dict(ticket: Ticket) -> Dict[str, Any]:
        """Convert ticket to dictionary"""
        
        # Build role details arrays
        role_ids = []
        role_names = []
        role_uuids = []
        
        if ticket.role_ids:
            from app.models.role import Role
            for rid in ticket.role_ids:
                role = Role.query.get(rid)
                if role:
                    role_uuids.append(str(role.id))
                    role_names.append(role.name)
                    role_ids.append(str(role.role_id) if hasattr(role, 'role_id') else str(role.id))
        
        return {
            "id": str(ticket.id),
            "ticketId": ticket.ticket_id,
            "ticketLink": ticket.ticket_link,
            "projectId": str(ticket.project_id) if ticket.project_id else None,
            "projectName": ticket.project.name if ticket.project else None,
            "roleIds": role_ids,
            "roleNames": role_names,
            "roleUuids": role_uuids,
            "employeeId": str(ticket.employee_id) if ticket.employee_id else None,
            "employeeName": ticket.employee.vn_full_name if ticket.employee else None,
            "employeeEmail": ticket.employee.email if ticket.employee else None,
            "ticketTypeId": str(ticket.ticket_type_id) if ticket.ticket_type_id else None,
            "ticketTypeName": ticket.ticket_type.name if ticket.ticket_type else None,
            "ticketStatusId": str(ticket.ticket_status_id) if ticket.ticket_status_id else None,
            "ticketStatusName": ticket.ticket_status.name if ticket.ticket_status else None,
            "week": ticket.week,
            "month": ticket.month,
            "createdAt": ticket.created_at.isoformat() if ticket.created_at else None,
            "updatedAt": ticket.updated_at.isoformat() if ticket.updated_at else None
        }

