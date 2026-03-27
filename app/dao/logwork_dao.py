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
        """Get logwork by UUID with employee eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee)
        ).filter_by(id=id).first()

    @staticmethod
    def get_all() -> List[Logwork]:
        """Get all logworks with employee eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee)
        ).all()
    
    @staticmethod
    def get_by_user_id(user_id: str) -> List[Logwork]:
        """Get all logworks for a specific user with employee eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee)
        ).filter_by(user_id=user_id).order_by(desc(Logwork.month)).all()
    
    @staticmethod
    def get_by_user_id_and_month(user_id: str, month: str) -> Optional[Logwork]:
        """Get logwork for a specific user in a specific month with employee eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee)
        ).filter(
            and_(Logwork.user_id == user_id, Logwork.month == month)
        ).first()

    @staticmethod
    def get_by_user_id_month_year(user_id: str, month: str, year: str) -> Optional[Logwork]:
        """Get logwork for a specific user in a specific month and year (used for upsert)"""
        return Logwork.query.options(
            joinedload(Logwork.employee)
        ).filter(
            and_(Logwork.user_id == user_id, Logwork.month == month, Logwork.year == year)
        ).first()
    
    @staticmethod
    def get_by_month(month: str) -> List[Logwork]:
        """Get all logworks for a specific month with employee eagerly loaded"""
        return Logwork.query.options(
            joinedload(Logwork.employee)
        ).filter_by(month=month).order_by(desc(Logwork.created_at)).all()
    
    @staticmethod
    def get_all_filtered(months: List[str] = None, quarter: str = None, year: str = None, user_eng_name: str = None, user_id: str = None, sort_by: str = None) -> List[Logwork]:
        """Get logworks with optional filters and sorting
        
        Args:
            months: Filter by list of months e.g. ['01', '03', '04'] (optional)
            quarter: Filter by quarter 1-4 (3 months), optional (ignored when months is provided)
            year: Filter by year (optional)
            user_eng_name: Filter by employee English name (optional, case-insensitive)
            user_id: Filter by user_id (optional)
            sort_by: Sort by loghours ('asc' or 'desc'), default is by created_at desc (optional)
        
        Returns:
            List of logworks matching filters
        """
        query = Logwork.query.options(joinedload(Logwork.employee))
        
        # Join with Employee table if filtering by name
        if user_eng_name:
            query = query.join(Employee, Logwork.user_id == Employee.id)
            query = query.filter(Employee.en_full_name.ilike(f'%{user_eng_name}%'))
        elif user_id:
            query = query.filter(Logwork.user_id == user_id)
        
        # Filter by year
        if year:
            query = query.filter(Logwork.year == year)
        
        # Filter by months list or quarter (months list takes precedence)
        if months:
            query = query.filter(Logwork.month.in_(months))
        elif quarter and quarter in LogworkDAO.QUARTER_MONTHS:
            quarter_months = LogworkDAO.QUARTER_MONTHS[quarter]
            query = query.filter(Logwork.month.in_(quarter_months))
        
        # Apply sorting
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
        result = query.scalar()
        return float(result) if result else 0.0

    # ---------- CREATE ----------
    @staticmethod
    def create(user_id: str, log_hours: Decimal, month: str, year: str = '2026') -> Logwork:
        """Create new logwork"""
        try:
            logwork = Logwork(
                user_id=user_id,
                loghours=log_hours,
                month=month,
                year=year
            )
            db.session.add(logwork)
            db.session.commit()
            return logwork
        except Exception:
            db.session.rollback()
            raise

    # ---------- UPDATE ----------
    @staticmethod
    def update(id: str, log_hours: Decimal = None, month: str = None, year: str = None) -> Logwork:
        """Update logwork"""
        try:
            logwork = LogworkDAO.get_by_id(id)
            
            if not logwork:
                raise ValueError("Logwork not found")
            
            # Update fields if provided
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
        except Exception:
            db.session.rollback()
            raise