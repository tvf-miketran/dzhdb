
from sqlalchemy import asc, desc, and_, or_, func
from sqlalchemy.orm import joinedload
from app.models.ticket import Ticket
from app.models.employee import Employee
from app.models.project import Project
from app import db
from typing import Optional, List


class TicketDAO:

    @staticmethod
    def _build_filtered_query(
        project_id: Optional[List[str]] = None,
        employee_id: Optional[List[str]] = None,
        ticket_type_id: Optional[List[str]] = None,
        ticket_status_id: Optional[List[str]] = None,
        week: Optional[List[int]] = None,
        month: Optional[List[int]] = None,
        search: Optional[str] = None,
        include_employee_search: bool = True,
    ):
        """Build filtered ticket query with role-specific search fields."""
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

        # Role-specific search behavior by endpoint:
        # - Admin route: ticket + project + employee fields
        # - My route: ticket_id + project_id only (no employee fields)
        if search:
            search_pattern = f"%{search}%"

            query = query.join(Ticket.project)

            search_conditions = [
                Ticket.ticket_id.ilike(search_pattern),
                Project.project_id.ilike(search_pattern),
            ]

            if include_employee_search:
                query = query.outerjoin(Ticket.employee)
                search_conditions.extend([
                    Ticket.ticket_link.ilike(search_pattern),
                    Project.name.ilike(search_pattern),
                    Employee.employeeId.ilike(search_pattern),
                    Employee.en_full_name.ilike(search_pattern),
                    Employee.vn_full_name.ilike(search_pattern),
                    Employee.email.ilike(search_pattern),
                ])

            query = query.filter(or_(*search_conditions))

        return query

    @staticmethod
    def _apply_sorting(query, sort_by: str = "created_at", sort_order: str = "desc"):
        """Apply ticket sorting to query."""
        sort_column = getattr(Ticket, sort_by, Ticket.created_at)
        if sort_order.lower() == "asc":
            return query.order_by(asc(sort_column))
        return query.order_by(desc(sort_column))

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
    def get_by_ticket_id_and_employee_id(ticket_id: str, employee_id: str) -> Optional[Ticket]:
        """Get ticket by ticket_id AND employee_id with relationships eagerly loaded
        
        Args:
            ticket_id: The ticket ID string
            employee_id: The employee UUID string
            
        Returns:
            Ticket if found with both matching ticket_id and employee_id, None otherwise
        """
        return Ticket.query.options(
            joinedload(Ticket.project),
            joinedload(Ticket.employee),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.ticket_status)
        ).filter_by(ticket_id=ticket_id, employee_id=employee_id).first()

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
    def count_by_filters(
        month: int,
        employee_id: Optional[str] = None,
        ticket_status_id: Optional[str] = None,
        active_only: bool = False,
        project_id: Optional[str] = None,
    ) -> int:
        """Count tickets by month with optional employee/status/project and active-employee filters."""
        query = Ticket.query.filter(Ticket.month == month)

        if employee_id:
            query = query.filter(Ticket.employee_id == employee_id)

        if ticket_status_id:
            query = query.filter(Ticket.ticket_status_id == ticket_status_id)

        if project_id:
            query = query.filter(Ticket.project_id == project_id)

        if active_only:
            query = query.filter(
                Ticket.employee.has(
                    and_(
                        Employee.status.is_(True),
                        Employee.authorize_role != "ADMIN",
                    )
                )
            )

        return query.count()

    @staticmethod
    def count_distinct_employees_with_tickets(
        month: int,
        project_id: Optional[str] = None,
    ) -> int:
        """Count distinct active non-admin employees that have at least one ticket in the given month."""
        query = (
            db.session.query(func.count(func.distinct(Ticket.employee_id)))
            .filter(Ticket.month == month)
            .filter(
                Ticket.employee.has(
                    Employee.authorize_role != "ADMIN",
                )
            )
        )
        if project_id:
            query = query.filter(Ticket.project_id == project_id)
        return query.scalar() or 0

    @staticmethod
    def get_by_month_and_status_active_non_admin(
        month: int,
        ticket_status_id: str,
    ) -> List[Ticket]:
        """Get tickets by month and status, limited to active non-admin employees."""
        return (
            Ticket.query
            .filter(Ticket.month == month)
            .filter(Ticket.ticket_status_id == ticket_status_id)
            .filter(
                Ticket.employee.has(
                    and_(
                        Employee.status.is_(True),
                        Employee.authorize_role != "ADMIN",
                    )
                )
            )
            .all()
        )
    
    @staticmethod
    def count_by_months_active(
        months: List[int],
        ticket_status_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> int:
        """Count tickets across months for active non-admin employees."""
        query = Ticket.query.filter(Ticket.month.in_(months))
        if ticket_status_id:
            query = query.filter(Ticket.ticket_status_id == ticket_status_id)
        if project_id:
            query = query.filter(Ticket.project_id == project_id)
        query = query.filter(
            Ticket.employee.has(
                and_(
                    Employee.status.is_(True),
                    Employee.authorize_role != "ADMIN",
                )
            )
        )
        return query.count()

    @staticmethod
    def count_distinct_by_months_active(
        months: List[int],
        ticket_status_id: Optional[str] = None,
        project_id: Optional[str] = None,
        ticket_type_ids: Optional[List[str]] = None,
    ) -> int:
        """Count distinct ticket_id values across months for active non-admin employees.

        Tickets assigned to multiple employees share the same ticket_id;
        this counts each unique ticket_id only once.
        """
        from sqlalchemy import func as sa_func

        query = db.session.query(
            sa_func.count(sa_func.distinct(Ticket.ticket_id))
        ).filter(Ticket.month.in_(months))
        if ticket_status_id:
            query = query.filter(Ticket.ticket_status_id == ticket_status_id)
        if project_id:
            query = query.filter(Ticket.project_id == project_id)
        if ticket_type_ids:
            query = query.filter(Ticket.ticket_type_id.in_(ticket_type_ids))
        query = query.filter(
            Ticket.employee.has(
                and_(
                    Employee.status.is_(True),
                    Employee.authorize_role != "ADMIN",
                )
            )
        )
        return query.scalar() or 0

    @staticmethod
    def count_by_project_employees_months(
        project_id: str,
        employee_ids: List[str],
        months: List[int],
        ticket_status_id: Optional[str] = None,
    ) -> int:
        """Count tickets for a project assigned to specific employees in given months."""
        if not employee_ids:
            return 0
        query = Ticket.query.filter(
            Ticket.project_id == project_id,
            Ticket.employee_id.in_(employee_ids),
            Ticket.month.in_(months),
        )
        if ticket_status_id:
            query = query.filter(Ticket.ticket_status_id == ticket_status_id)
        return query.count()

    @staticmethod
    def get_by_employee_month_status(
        employee_id: str,
        month: int,
        ticket_status_id: str,
        project_id: Optional[str] = None,
    ) -> List[Ticket]:
        """Get tickets for a specific employee, month and status, with optional project filter."""
        query = Ticket.query.filter(
            Ticket.employee_id == employee_id,
            Ticket.month == month,
            Ticket.ticket_status_id == ticket_status_id,
        )
        if project_id:
            query = query.filter(Ticket.project_id == project_id)
        return query.all()

    @staticmethod
    def get_by_month_status_active(
        month: int,
        ticket_status_id: str,
        project_id: Optional[str] = None,
        ticket_type_ids: Optional[List[str]] = None,
    ) -> List[Ticket]:
        """Get tickets by month and status for active non-admin employees, with optional project/type filter."""
        query = (
            Ticket.query
            .filter(Ticket.month == month)
            .filter(Ticket.ticket_status_id == ticket_status_id)
            .filter(
                Ticket.employee.has(
                    and_(
                        Employee.status.is_(True),
                        Employee.authorize_role != "ADMIN",
                    )
                )
            )
        )
        if project_id:
            query = query.filter(Ticket.project_id == project_id)
        if ticket_type_ids:
            query = query.filter(Ticket.ticket_type_id.in_(ticket_type_ids))
        return query.all()

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
        """Get filtered and sorted tickets with pagination (Admin search scope).
        
        Args:
            project_id: List of project UUIDs or single project UUID (can be comma-separated string or list)
            employee_id: List of employee UUIDs or single employee UUID
            ticket_type_id: List of ticket type UUIDs or single ticket type UUID
            ticket_status_id: List of ticket status UUIDs or single ticket status UUID
            week: List of week numbers or single week number
            month: List of month numbers or single month number
        """
        query = TicketDAO._build_filtered_query(
            project_id=project_id,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month,
            search=search,
            include_employee_search=True
        )
        query = TicketDAO._apply_sorting(query, sort_by=sort_by, sort_order=sort_order)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_my_filtered_sorted(
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
        """Get filtered and sorted tickets with pagination (Member search scope)."""
        query = TicketDAO._build_filtered_query(
            project_id=project_id,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month,
            search=search,
            include_employee_search=False
        )
        query = TicketDAO._apply_sorting(query, sort_by=sort_by, sort_order=sort_order)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_all_filtered(
        project_id: Optional[List[str]] = None,
        employee_id: Optional[List[str]] = None,
        ticket_type_id: Optional[List[str]] = None,
        ticket_status_id: Optional[List[str]] = None,
        week: Optional[List[int]] = None,
        month: Optional[List[int]] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Ticket]:
        """Get all filtered tickets without pagination (Admin search scope)."""
        query = TicketDAO._build_filtered_query(
            project_id=project_id,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month,
            search=search,
            include_employee_search=True
        )
        query = TicketDAO._apply_sorting(query, sort_by=sort_by, sort_order=sort_order)
        return query.all()

    @staticmethod
    def get_my_filtered(
        project_id: Optional[List[str]] = None,
        employee_id: Optional[List[str]] = None,
        ticket_type_id: Optional[List[str]] = None,
        ticket_status_id: Optional[List[str]] = None,
        week: Optional[List[int]] = None,
        month: Optional[List[int]] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Ticket]:
        """Get all filtered tickets without pagination (Member search scope)."""
        query = TicketDAO._build_filtered_query(
            project_id=project_id,
            employee_id=employee_id,
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month,
            search=search,
            include_employee_search=False
        )
        query = TicketDAO._apply_sorting(query, sort_by=sort_by, sort_order=sort_order)
        return query.all()
    
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

