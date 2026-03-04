
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload
from app.models.ticket import Ticket
from app import db
from typing import Optional, List


class TicketDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[Ticket]:
        """Get ticket by UUID with relationships eagerly loaded"""
        return Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        ).filter_by(id=id).first()

    @staticmethod
    def get_by_ticket_id(ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ticket_id (string) with relationships eagerly loaded"""
        return Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        ).filter_by(ticket_id=ticket_id).first()

    @staticmethod
    def get_by_ticket_id_like(ticket_id_pattern: str) -> List[Ticket]:
        """Get tickets by ticket_id pattern using LIKE search
        
        Args:
            ticket_id_pattern: The pattern to search for (e.g., "ABC-123" will match "ABC-123", "ABC-123(1)", "ABC-123(2)")
        
        Returns:
            List of tickets matching the pattern
        """
        # Use ILIKE for case-insensitive search
        search_pattern = f"{ticket_id_pattern}%"
        return Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        ).filter(Ticket.ticket_id.ilike(search_pattern)).all()
    
    @staticmethod
    def get_all() -> List[Ticket]:
        """Get all tickets with relationships eagerly loaded"""
        return Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        ).all()
    
    @staticmethod
    def get_by_project_id(project_id: str) -> List[Ticket]:
        """Get all tickets for a project with relationships eagerly loaded"""
        return Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        ).filter_by(project_id=project_id).all()
    
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
    ):
        """Get filtered and sorted tickets with pagination
        
        Args:
            project_id: List of project UUIDs or single project UUID (can be comma-separated string or list)
            employee_id: List of employee UUIDs or single employee UUID
            ticket_type_id: List of ticket type UUIDs or single ticket type UUID
            ticket_status_id: List of ticket status UUIDs or single ticket status UUID
            week: List of week numbers or single week number
            month: List of month numbers or single month number
        """
        query = Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        )

        # Filter by project(s) - support both single and multiple values
        if project_id:
            if len(project_id) == 1:
                query = query.filter(Ticket.project_id == project_id[0])
            else:
                query = query.filter(Ticket.project_id.in_(project_id))

        # Filter by employee(s) - support both single and multiple values
        if employee_id:
            if len(employee_id) == 1:
                query = query.filter(Ticket.employee_id == employee_id[0])
            else:
                query = query.filter(Ticket.employee_id.in_(employee_id))

        # Filter by ticket type(s) - support both single and multiple values
        if ticket_type_id:
            if len(ticket_type_id) == 1:
                query = query.filter(Ticket.ticket_type_id == ticket_type_id[0])
            else:
                query = query.filter(Ticket.ticket_type_id.in_(ticket_type_id))

        # Filter by ticket status(es) - support both single and multiple values
        if ticket_status_id:
            if len(ticket_status_id) == 1:
                query = query.filter(Ticket.ticket_status_id == ticket_status_id[0])
            else:
                query = query.filter(Ticket.ticket_status_id.in_(ticket_status_id))

        # Filter by week(s) - support both single and multiple values
        if week is not None and len(week) > 0:
            if len(week) == 1:
                query = query.filter(Ticket.week == week[0])
            else:
                query = query.filter(Ticket.week.in_(week))

        # Filter by month(s) - support both single and multiple values
        if month is not None and len(month) > 0:
            if len(month) == 1:
                query = query.filter(Ticket.month == month[0])
            else:
                query = query.filter(Ticket.month.in_(month))

        # Search in ticket_id, ticket_link
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Ticket.ticket_id.ilike(search_pattern),
                    Ticket.ticket_link.ilike(search_pattern)
                )
            )

        # Apply sorting
        sort_column = getattr(Ticket, sort_by, Ticket.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    # ---------- CREATE ----------
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
    ) -> Ticket:
        """Create new ticket"""
        try:
            ticket = Ticket(
                ticket_id=ticket_id,
                project_id=project_id,
                ticket_link=ticket_link,
                role_ids=role_ids or [],
                employee_id=employee_id,
                ticket_type_id=ticket_type_id,
                ticket_status_id=ticket_status_id,
                week=week,
                month=month
            )
            db.session.add(ticket)
            db.session.commit()
            return ticket
        except Exception:
            db.session.rollback()
            raise

    # ---------- UPDATE ----------
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
    ) -> Ticket:
        """Update ticket"""
        try:
            ticket = TicketDAO.get_by_id(id)
            
            if not ticket:
                raise ValueError("Ticket not found")
            
            # Note: ticket_id uniqueness check removed - duplicate ticket_ids are now allowed
            
            # Update fields
            if ticket_id is not None:
                ticket.ticket_id = ticket_id
            
            if ticket_link is not None:
                ticket.ticket_link = ticket_link
            
            if project_id is not None:
                ticket.project_id = project_id
            
            if role_ids is not None:
                ticket.role_ids = role_ids
            
            if employee_id is not None:
                ticket.employee_id = employee_id
            
            if ticket_type_id is not None:
                ticket.ticket_type_id = ticket_type_id
            
            if ticket_status_id is not None:
                ticket.ticket_status_id = ticket_status_id
            
            if week is not None:
                ticket.week = week
            
            if month is not None:
                ticket.month = month
            
            db.session.commit()
            return ticket
        except Exception:
            db.session.rollback()
            raise

    # ---------- DELETE ----------
    @staticmethod
    def delete(id: str) -> bool:
        """Delete ticket by UUID"""
        try:
            ticket = TicketDAO.get_by_id(id)
            
            if not ticket:
                return False
            
            db.session.delete(ticket)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

