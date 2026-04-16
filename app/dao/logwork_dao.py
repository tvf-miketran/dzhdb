from sqlalchemy import asc, desc, and_
from sqlalchemy.orm import joinedload
from app.models.logwork import Logwork
from app.models.employee import Employee
from app import db
from typing import Optional, List
from decimal import Decimal


class LogworkDAO:

    # Quarter to months mapping
    QUARTER_MONTHS = {
        '1': ['01', '02', '03'],
        '2': ['04', '05', '06'],
        '3': ['07', '08', '09'],
        '4': ['10', '11', '12']
    }

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[Logwork]:
        """Get logwork by UUID with employee and project eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee),
            joinedload(Logwork.project),
        ).filter_by(id=id).first()

    @staticmethod
    def get_all() -> List[Logwork]:
        """Get all logworks with employee and project eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee),
            joinedload(Logwork.project),
        ).all()

    @staticmethod
    def get_by_user_id(user_id: str) -> List[Logwork]:
        """Get all logworks for a specific user with employee and project eagerly loaded"""
        return (
            Logwork.query
            .options(joinedload(Logwork.employee), joinedload(Logwork.project))
            .filter_by(user_id=user_id)
            .order_by(desc(Logwork.year), desc(Logwork.month), desc(Logwork.created_at))
            .all()
        )

    @staticmethod
    def get_by_user_id_and_month(
        user_id: str,
        month: str,
        year: str = None,
        project_id: str = None,
    ) -> Optional[Logwork]:
        """Get logwork for a specific user in a specific month with optional year/project filters."""
        filters = [Logwork.user_id == user_id, Logwork.month == month]
        if year is not None:
            filters.append(Logwork.year == year)
        if project_id is not None:
            filters.append(Logwork.project_id == project_id)

        return (
            Logwork.query
            .options(joinedload(Logwork.employee), joinedload(Logwork.project))
            .filter(and_(*filters))
            .first()
        )

    @staticmethod
    def get_by_user_id_month_year(
        user_id: str,
        month: str,
        year: str,
        project_id: str = None,
    ) -> Optional[Logwork]:
        """Get logwork for a specific user in a specific month/year, optionally scoped to a project."""
        filters = [Logwork.user_id == user_id, Logwork.month == month, Logwork.year == year]
        if project_id is not None:
            filters.append(Logwork.project_id == project_id)

        return (
            Logwork.query
            .options(joinedload(Logwork.employee), joinedload(Logwork.project))
            .filter(and_(*filters))
            .first()
        )

    @staticmethod
    def get_by_month(month: str) -> List[Logwork]:
        """Get all logworks for a specific month with employee and project eagerly loaded"""
        return (
            Logwork.query
            .options(joinedload(Logwork.employee), joinedload(Logwork.project))
            .filter_by(month=month)
            .order_by(desc(Logwork.created_at))
            .all()
        )

    @staticmethod
    def get_all_filtered(
        months: List[str] = None,
        quarter: str = None,
        year: str = None,
        user_eng_name: str = None,
        user_id: str = None,
        project_id: str = None,
        sort_by: str = None,
    ) -> List[Logwork]:
        """Get logworks with optional filters and sorting"""
        query = Logwork.query.options(
            joinedload(Logwork.employee),
            joinedload(Logwork.project),
        )

        # Join with Employee table if filtering by name
        if user_eng_name:
            query = query.join(Employee, Logwork.user_id == Employee.id)
            query = query.filter(Employee.en_full_name.ilike(f'%{user_eng_name}%'))
        elif user_id:
            query = query.filter(Logwork.user_id == user_id)

        if project_id:
            query = query.filter(Logwork.project_id == project_id)

        if year:
            query = query.filter(Logwork.year == year)

        if months:
            query = query.filter(Logwork.month.in_(months))
        elif quarter and quarter in LogworkDAO.QUARTER_MONTHS:
            query = query.filter(Logwork.month.in_(LogworkDAO.QUARTER_MONTHS[quarter]))

        if sort_by == 'asc':
            query = query.order_by(asc(Logwork.loghours))
        elif sort_by == 'desc':
            query = query.order_by(desc(Logwork.loghours))
        else:
            query = query.order_by(desc(Logwork.created_at))

        return query.all()

    @staticmethod
    def sum_hours_by_user_ids_months(
        user_ids: List[str],
        months: List[str],
        year: str = None,
        project_id: str = None,
    ) -> float:
        """Sum logwork hours for given user IDs across given months."""
        from sqlalchemy import func as sa_func

        if not user_ids or not months:
            return 0.0
        query = db.session.query(
            sa_func.coalesce(sa_func.sum(Logwork.loghours), 0)
        ).filter(
            Logwork.user_id.in_(user_ids),
            Logwork.month.in_(months),
        )
        if year:
            query = query.filter(Logwork.year == year)
        if project_id:
            query = query.filter(Logwork.project_id == project_id)
        result = query.scalar()
        return float(result) if result else 0.0

    @staticmethod
    def get_distinct_user_ids_with_logwork(
        month: str,
        year: str = None,
        project_id: str = None,
    ) -> set[str]:
        """Return distinct non-admin employee IDs that have logwork in the given month."""
        query = (
            db.session.query(Logwork.user_id)
            .filter(Logwork.month == month)
            .filter(
                Logwork.employee.has(
                    Employee.authorize_role != "ADMIN",
                )
            )
            .distinct()
        )
        if year:
            query = query.filter(Logwork.year == year)
        if project_id:
            query = query.filter(Logwork.project_id == project_id)

        return {str(user_id) for (user_id,) in query.all() if user_id is not None}

    # ---------- CREATE ----------
    @staticmethod
    def create(
        user_id: str,
        project_id: str,
        log_hours: Decimal,
        month: str,
        year: str = '2026',
    ) -> Logwork:
        """Create new logwork"""
        try:
            logwork = Logwork(
                user_id=user_id,
                project_id=project_id,
                loghours=log_hours,
                month=month,
                year=year,
            )
            db.session.add(logwork)
            db.session.commit()
            return logwork
        except Exception:
            db.session.rollback()
            raise

    # ---------- UPDATE ----------
    @staticmethod
    def update(
        id: str,
        project_id: Optional[str] = None,
        log_hours: Optional[Decimal] = None,
        month: Optional[str] = None,
        year: Optional[str] = None,
    ) -> Logwork:
        """Update logwork"""
        try:
            logwork = LogworkDAO.get_by_id(id)
            if not logwork:
                raise ValueError("Logwork not found")

            if project_id is not None:
                logwork.project_id = project_id
            if log_hours is not None:
                logwork.loghours = log_hours
            if month is not None:
                logwork.month = month
            if year is not None:
                logwork.year = year

            db.session.commit()
            return logwork
        except Exception:
            db.session.rollback()
            raise

    # ---------- DELETE ----------
    @staticmethod
    def delete(id: str) -> bool:
        """Delete logwork by ID"""
        try:
            logwork = LogworkDAO.get_by_id(id)
            if not logwork:
                raise ValueError("Logwork not found")
            db.session.delete(logwork)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise