
from typing import Optional, List, Dict, Any, Tuple
from app.dao.ticket_dao import TicketDAO
from app.dao.project_dao import ProjectDAO
from app.dao.employee_dao import EmployeeDAO
from app.dao.role_dao import RoleDAO
from app.models.ticket import Ticket
from app.requests.ticket_request import parse_week_string, validate_week_in_month


class TicketService:
    @staticmethod
    def _can_adjust_ticket(ticket: Ticket, current_user_id: str, current_user_role: Optional[str]) -> bool:
        """A ticket can be deleted only by admin or ticket owner."""
        if RoleDAO._is_admin(current_user_role):
            return True

        if not ticket or not ticket.employee_id or not current_user_id:
            return False

        return str(ticket.employee_id) == str(current_user_id)

    @staticmethod
    def _resolve_role_ids(role_ids: Optional[List[str]]) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """Resolve roleID strings (like 'DEV', 'BA') to UUIDs
        
        Args:
            role_ids: List of roleID strings or UUIDs
            
        Returns:
            Tuple of (resolved_role_uuids, error_messages)
        """
        if not role_ids:
            return None, None
        
        resolved_uuids = []
        errors = []
        
        for role_id in role_ids:
            # Try to resolve using RoleDAO
            resolved_uuid, error = RoleDAO._resolve_role_id(role_id)
            if error:
                errors.append(error)
            else:
                resolved_uuids.append(resolved_uuid)
        
        if errors:
            return None, errors
        
        return resolved_uuids, None

    @staticmethod
    def _validate_foreign_keys(
        project_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        role_ids: Optional[List[str]] = None,
        ticket_type_id: Optional[str] = None,
        ticket_status_id: Optional[str] = None,
        resolve_role_ids: bool = True
    ) -> List[str]:
        """Validate that all foreign key references exist
        
        Args:
            resolve_role_ids: If True, resolve roleID strings to UUIDs before validation
        
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
        # Resolve roleID strings to UUIDs first
        resolved_role_ids = role_ids
        if role_ids and resolve_role_ids:
            resolved_role_ids, resolve_errors = TicketService._resolve_role_ids(role_ids)
            if resolve_errors:
                errors.extend(resolve_errors)
                resolved_role_ids = None  # Don't validate if resolution failed
        
        if resolved_role_ids:
            if isinstance(resolved_role_ids, list):
                for role_id in resolved_role_ids:
                    role = RoleDAO.get_by_id(role_id)
                    if not role:
                        errors.append(f"Role with ID '{role_id}' not found")
            else:
                # Single role_id (backward compatibility)
                role = RoleDAO.get_by_id(resolved_role_ids)
                if not role:
                    errors.append(f"Role with ID '{resolved_role_ids}' not found")
        
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
    def get_by_ticket_id_like(ticket_id_pattern: str) -> List[Ticket]:
        """Get tickets by ticket_id pattern using LIKE search
        
        Args:
            ticket_id_pattern: The pattern to search for (e.g., "ABC-123" will match "ABC-123", "ABC-123(1)", "ABC-123(2)")
        
        Returns:
            List of tickets matching the pattern
        """
        return TicketDAO.get_by_ticket_id_like(ticket_id_pattern)
    
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
        """Create new ticket with validation. If ticket_id exists, return error.
        
        Note: role_ids can be roleID strings (BA, DEV, EQA, IQA, REVIEWER) which
              will be resolved to UUIDs internally.
        
        Returns:
            Tuple of (ticket, errors, message). If ticket_id exists, returns error with message.
        """
        errors = []
        message = None
        
        # Check if ticket with same ticket_id AND employee_id already exists
        # If both ticket_id AND employee_id match, then ticket is considered duplicate
        # If only ticket_id matches but employee_id is different, allow creating new ticket
        if employee_id:
            existing_ticket = TicketDAO.get_by_ticket_id_and_employee_id(ticket_id, employee_id)
            if existing_ticket:
                return None, ["Ticket ID already exists for this employee"], "ticket already exist for this employee, please go to update page"
        else:
            # If no employee_id provided, check if ticket_id exists (original behavior)
            existing_ticket = TicketDAO.get_by_ticket_id(ticket_id)
            if existing_ticket:
                return None, ["Ticket ID already exists"], "ticket already exist, please go to update page"
        
        # Resolve role IDs to UUIDs (roleID like 'DEV' -> UUID)
        resolved_role_ids = None
        if role_ids:
            resolved_role_ids, resolve_errors = TicketService._resolve_role_ids(role_ids)
            if resolve_errors:
                return None, resolve_errors, None
        
        # Validate foreign keys (with resolved role IDs)
        fk_errors = TicketService._validate_foreign_keys(
            project_id=project_id,
            employee_id=employee_id,
            role_ids=resolved_role_ids,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            resolve_role_ids=False  # Already resolved above
        )
        errors.extend(fk_errors)
        
        if errors:
            return None, errors, None
        
        try:
            ticket = TicketDAO.create(
                ticket_id=ticket_id,
                project_id=project_id,
                ticket_link=ticket_link,
                role_ids=resolved_role_ids,
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
    def create_bulk(
        tickets_data: List[Dict[str, Any]]
    ) -> Tuple[List[Ticket], List[Dict[str, Any]], List[str]]:
        """Create multiple tickets, handling mixed existing/new tickets
        
        Args:
            tickets_data: List of ticket dictionaries with the same fields as create()
                     Note: role_ids can now be roleID strings (BA, DEV, EQA, IQA, REVIEWER)
                     which will be resolved to UUIDs internally.
        
        Returns:
            Tuple of (created_tickets, existing_tickets, errors)
            - created_tickets: List of successfully created tickets
            - existing_tickets: List of dicts with ticket_id and ticket data for existing tickets
            - errors: List of error messages for failed creations
        """
        created_tickets = []
        existing_tickets = []
        errors = []
        
        for idx, ticket_data in enumerate(tickets_data):
            ticket_id = ticket_data.get("ticket_id")
            employee_id = ticket_data.get("employee_id")
            
            # Check if ticket with same ticket_id AND employee_id already exists
            # If both ticket_id AND employee_id match, then ticket is considered duplicate
            # If only ticket_id matches but employee_id is different, allow creating new ticket
            if employee_id:
                existing_ticket = TicketDAO.get_by_ticket_id_and_employee_id(ticket_id, employee_id)
                if existing_ticket:
                    existing_tickets.append({
                        "ticketId": ticket_id,
                        "ticket": TicketService._to_dict(existing_ticket)
                    })
                    continue
            else:
                # If no employee_id provided, check if ticket_id exists (original behavior)
                existing_ticket = TicketDAO.get_by_ticket_id(ticket_id)
                if existing_ticket:
                    existing_tickets.append({
                        "ticketId": ticket_id,
                        "ticket": TicketService._to_dict(existing_ticket)
                    })
                    continue
            
            # Resolve role IDs to UUIDs (roleID like 'DEV' -> UUID)
            resolved_role_ids = None
            role_ids_input = ticket_data.get("role_ids")
            if role_ids_input:
                resolved_role_ids, resolve_errors = TicketService._resolve_role_ids(role_ids_input)
                if resolve_errors:
                    errors.append({
                        "index": idx,
                        "ticketId": ticket_id,
                        "errors": resolve_errors
                    })
                    continue
            
            # Validate foreign keys (with resolved role IDs)
            fk_errors = TicketService._validate_foreign_keys(
                project_id=ticket_data.get("project_id"),
                employee_id=ticket_data.get("employee_id"),
                role_ids=resolved_role_ids,
                ticket_type_id=ticket_data.get("ticket_type_id"),
                ticket_status_id=ticket_data.get("ticket_status_id"),
                resolve_role_ids=False  # Already resolved above
            )
            
            if fk_errors:
                errors.append({
                    "index": idx,
                    "ticketId": ticket_id,
                    "errors": fk_errors
                })
                continue
            
            try:
                ticket = TicketDAO.create(
                    ticket_id=ticket_id,
                    project_id=ticket_data.get("project_id"),
                    ticket_link=ticket_data.get("ticket_link"),
                    role_ids=resolved_role_ids,
                    employee_id=ticket_data.get("employee_id"),
                    ticket_type_id=ticket_data.get("ticket_type_id"),
                    ticket_status_id=ticket_data.get("ticket_status_id"),
                    week=ticket_data.get("week"),
                    month=ticket_data.get("month")
                )
                created_tickets.append(ticket)
            except Exception as e:
                errors.append({
                    "index": idx,
                    "ticketId": ticket_id,
                    "errors": [str(e)]
                })
        
        return created_tickets, existing_tickets, errors
    
    @staticmethod
    def update(
        id: str,
        current_user_id: str,
        current_user_role: Optional[str] = None,
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
        """Update ticket by UUID only
        
        Note: role_ids can be roleID strings (BA, DEV, EQA, IQA, REVIEWER) which
              will be resolved to UUIDs internally.
        
        Note: week accepts either integer (1, 2, 3) or string like "5 (12/01/2026-18/01/2026)"
        """
        # Try to get by UUID only
        ticket = TicketDAO.get_by_id(id)
        
        if not ticket:
            return None, ["Ticket not found"]

        if not TicketService._can_adjust_ticket(ticket, current_user_id, current_user_role):
            return None, ["Not authorized to update this ticket"]
        
        errors = []
        
        # Parse week string if it's a string (e.g., "5 (12/01/2026-18/01/2026)")
        parsed_week = week
        if week is not None and isinstance(week, str):
            parsed_week, week_error = parse_week_string(week)
            if week_error:
                return None, [week_error]
        
        # Validate week exists in the month (if both are provided)
        if parsed_week and month:
            week_error = validate_week_in_month(parsed_week, month)
            if week_error:
                return None, [week_error]
        
        # Resolve role IDs to UUIDs (roleID like 'DEV' -> UUID)
        resolved_role_ids = None
        if role_ids:
            resolved_role_ids, resolve_errors = TicketService._resolve_role_ids(role_ids)
            if resolve_errors:
                return None, resolve_errors
        
        # Validate foreign keys (only if provided)
        fk_errors = TicketService._validate_foreign_keys(
            project_id=project_id,
            employee_id=employee_id,
            role_ids=resolved_role_ids,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            resolve_role_ids=False  # Already resolved above
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
                role_ids=resolved_role_ids,
                employee_id=employee_id,
                ticket_type_id=ticket_type_id,
                ticket_status_id=ticket_status_id,
                week=parsed_week,
                month=month
            )
            return updated, None
        except Exception as e:
            return None, [str(e)]

    @staticmethod
    def update_bulk(
        tickets_data: List[Dict[str, Any]],
        current_user_id: str,
        current_user_role: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Update multiple tickets
        
        Args:
            tickets_data: List of ticket dictionaries with:
                - id: UUID or ticket_id to identify the ticket (required)
                - ticketId: New ticket ID (optional)
                - ticketLink: New ticket link (optional)
                - projectId: New project ID (optional)
                - roleIds: New role IDs array (optional, accepts roleID strings like BA, DEV)
                - employeeId: New employee ID (optional)
                - ticketTypeId: New ticket type ID (optional)
                - ticketStatusId: New ticket status ID (optional)
                - week: New week (optional)
                - month: New month (optional)
        
        Returns:
            Tuple of (updated_tickets, not_found_tickets, errors)
            - updated_tickets: List of successfully updated tickets
            - not_found_tickets: List of ticket IDs that were not found
            - errors: List of error messages for failed updates
        """
        updated_tickets = []
        not_found_tickets = []
        errors = []
        
        for idx, ticket_data in enumerate(tickets_data):
            # Get the identifier - must be UUID (id field)
            ticket_uuid = ticket_data.get("id")
            
            if not ticket_uuid:
                errors.append({
                    "index": idx,
                    "errors": ["Ticket UUID (id) is required"]
                })
                continue
            
            # Try to find the ticket by UUID only
            ticket = None
            try:
                ticket = TicketDAO.get_by_id(ticket_uuid)
            except Exception:
                pass
            
            if not ticket:
                not_found_tickets.append({
                    "index": idx,
                    "id": ticket_uuid,
                    "message": "Ticket not found"
                })
                continue

            if not TicketService._can_adjust_ticket(ticket, current_user_id, current_user_role):
                errors.append({
                    "index": idx,
                    "ticketId": ticket_uuid,
                    "code": "forbidden",
                    "errors": ["Not authorized to update this ticket"]
                })
                continue
            
            # Extract update fields (only include non-None values)
            update_fields = {}
            if "ticketId" in ticket_data and ticket_data["ticketId"] is not None:
                update_fields["ticket_id"] = ticket_data["ticketId"]
            if "ticketLink" in ticket_data and ticket_data["ticketLink"] is not None:
                update_fields["ticket_link"] = ticket_data["ticketLink"]
            if "projectId" in ticket_data and ticket_data["projectId"] is not None:
                update_fields["project_id"] = ticket_data["projectId"]
            if "employeeId" in ticket_data and ticket_data["employeeId"] is not None:
                update_fields["employee_id"] = ticket_data["employeeId"]
            if "ticketTypeId" in ticket_data and ticket_data["ticketTypeId"] is not None:
                update_fields["ticket_type_id"] = ticket_data["ticketTypeId"]
            if "ticketStatusId" in ticket_data and ticket_data["ticketStatusId"] is not None:
                update_fields["ticket_status_id"] = ticket_data["ticketStatusId"]
            
            # Handle week - parse string like "5 (12/01/2026-18/01/2026)" to integer
            if "week" in ticket_data and ticket_data["week"] is not None:
                week_str = ticket_data["week"]
                week, week_error = parse_week_string(week_str)
                if week_error:
                    errors.append({
                        "index": idx,
                        "ticketId": ticket_uuid,
                        "errors": [week_error]
                    })
                    continue
                update_fields["week"] = week
            
            # Handle month - validate it's between 1-12
            if "month" in ticket_data and ticket_data["month"] is not None:
                try:
                    month_val = int(ticket_data["month"])
                    if month_val < 1 or month_val > 12:
                        errors.append({
                            "index": idx,
                            "ticketId": ticket_uuid,
                            "errors": ["Month must be between 1 and 12"]
                        })
                        continue
                    update_fields["month"] = month_val
                except (ValueError, TypeError):
                    errors.append({
                        "index": idx,
                        "ticketId": ticket_uuid,
                        "errors": ["Invalid month format"]
                    })
                    continue
            
            # Validate week exists in the month (if both are provided)
            if "week" in update_fields and "month" in update_fields:
                week_error = validate_week_in_month(update_fields["week"], update_fields["month"])
                if week_error:
                    errors.append({
                        "index": idx,
                        "ticketId": ticket_uuid,
                        "errors": [week_error]
                    })
                    continue
            
            # Handle role_ids - resolve roleID strings to UUIDs
            resolved_role_ids = None
            role_ids_input = ticket_data.get("roleIds")
            if role_ids_input is not None:
                resolved_role_ids, resolve_errors = TicketService._resolve_role_ids(role_ids_input)
                if resolve_errors:
                    errors.append({
                        "index": idx,
                        "ticketId": ticket_uuid,
                        "errors": resolve_errors
                    })
                    continue
                update_fields["role_ids"] = resolved_role_ids
            
            # Skip if no fields to update
            if not update_fields:
                # Return the ticket as-is since there's nothing to update
                updated_tickets.append(TicketService._to_dict(ticket))
                continue
            
            # Validate foreign keys (only if provided in update_fields)
            fk_errors = TicketService._validate_foreign_keys(
                project_id=update_fields.get("project_id"),
                employee_id=update_fields.get("employee_id"),
                role_ids=update_fields.get("role_ids"),
                ticket_type_id=update_fields.get("ticket_type_id"),
                ticket_status_id=update_fields.get("ticket_status_id"),
                resolve_role_ids=False  # Already resolved above
            )
            
            if fk_errors:
                errors.append({
                    "index": idx,
                    "ticketId": ticket_uuid,
                    "errors": fk_errors
                })
                continue
            
            try:
                updated = TicketDAO.update(
                    id=str(ticket.id),
                    **update_fields
                )
                updated_tickets.append(TicketService._to_dict(updated))
            except Exception as e:
                errors.append({
                    "index": idx,
                    "ticketId": ticket_uuid,
                    "errors": [str(e)]
                })
        
        return updated_tickets, not_found_tickets, errors
    
    @staticmethod
    def delete(
        id: str,
        current_user_id: str,
        current_user_role: Optional[str] = None
    ) -> Tuple[bool, Optional[List[str]]]:
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

        if not TicketService._can_adjust_ticket(ticket, current_user_id, current_user_role):
            return False, ["Not authorized to delete this ticket"]
        
        try:
            deleted = TicketDAO.delete(str(ticket.id))
            return deleted, None
        except Exception as e:
            return False, [str(e)]

    @staticmethod
    def delete_bulk(
        ids: List[str],
        current_user_id: str,
        current_user_role: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Delete multiple tickets by UUID or ticket_id

        Args:
            ids: List of ticket identifiers (UUID or ticket_id)

        Returns:
            Tuple of (deleted_tickets, not_found_tickets, errors)
        """
        deleted_tickets = []
        not_found_tickets = []
        errors = []

        for idx, ticket_identifier in enumerate(ids):
            if ticket_identifier is None:
                errors.append({
                    "index": idx,
                    "id": ticket_identifier,
                    "errors": ["Ticket identifier is required"]
                })
                continue

            ticket_identifier = str(ticket_identifier).strip()
            if not ticket_identifier:
                errors.append({
                    "index": idx,
                    "id": ticket_identifier,
                    "errors": ["Ticket identifier is required"]
                })
                continue

            # Try to get by UUID first, then by ticket_id
            ticket = TicketDAO.get_by_id(ticket_identifier)
            if not ticket:
                ticket = TicketDAO.get_by_ticket_id(ticket_identifier)

            if not ticket:
                not_found_tickets.append({
                    "index": idx,
                    "id": ticket_identifier,
                    "message": "Ticket not found"
                })
                continue

            if not TicketService._can_adjust_ticket(ticket, current_user_id, current_user_role):
                errors.append({
                    "index": idx,
                    "id": ticket_identifier,
                    "ticketId": ticket.ticket_id,
                    "code": "forbidden",
                    "errors": ["Not authorized to delete this ticket"]
                })
                continue

            try:
                deleted = TicketDAO.delete(str(ticket.id))
                if deleted:
                    deleted_tickets.append({
                        "index": idx,
                        "id": ticket_identifier,
                        "deletedId": str(ticket.id),
                        "ticketId": ticket.ticket_id
                    })
                else:
                    errors.append({
                        "index": idx,
                        "id": ticket_identifier,
                        "errors": ["Failed to delete ticket"]
                    })
            except Exception as e:
                errors.append({
                    "index": idx,
                    "id": ticket_identifier,
                    "errors": [str(e)]
                })

        return deleted_tickets, not_found_tickets, errors
    
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
            "employeeEngName": ticket.employee.en_full_name if ticket.employee else None,
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