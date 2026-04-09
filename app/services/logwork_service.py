from typing import Optional, List, Dict, Any, Tuple
from app.dao.logwork_dao import LogworkDAO
from app.dao.formula_dao import FormulaDAO
from app.dao.project_dao import ProjectDAO
from app.models.logwork import Logwork
from app.models.employee import Employee
from app.requests.logwork_request import CreateLogworkRequest, UpdateLogworkRequest
from decimal import Decimal


class LogworkService:

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_standard_logwork_by_month(month: str) -> float:
        """Get STANDARD_LOGWORK value for a month."""
        try:
            month_num = int(month)
        except (TypeError, ValueError):
            return 0.0

        value = FormulaDAO.get_param("STANDARD_LOGWORK", month_num)
        return LogworkService._safe_float(value, 0.0)

    @staticmethod
    def _get_total_ee_percent_by_user(user_id: str) -> float:
        """Get total EE percent for a user across all project memberships."""
        memberships = ProjectDAO.get_all_memberships_by_user(user_id)
        return sum(
            LogworkService._safe_float(membership.allocation_percent, 0.0)
            for membership in memberships
        )

    @staticmethod
    def _build_metrics(logwork: Logwork) -> Dict[str, Any]:
        """Build status and estimate metrics for a logwork row."""
        standard_logwork = LogworkService._get_standard_logwork_by_month(logwork.month)
        total_ee_percent = LogworkService._get_total_ee_percent_by_user(str(logwork.user_id))
        ee_ratio = total_ee_percent / 100.0

        estimate_score = 0.0
        denominator = standard_logwork * ee_ratio
        if denominator > 0:
            estimate_score = float(logwork.loghours) / denominator

        return {
            "standardLogworkInMonth": standard_logwork,
            "totalEEPercent": total_ee_percent,
            "estimateScore": round(estimate_score, 4),
            "status": 1 if estimate_score >= 1 else 0,
        }

    @staticmethod
    def to_dict_with_metrics(logwork: Logwork) -> Dict[str, Any]:
        """Convert a logwork object to response dict with estimate metrics."""
        data = LogworkService._to_dict(logwork)
        data.update(LogworkService._build_metrics(logwork))
        return data

    @staticmethod
    def to_list_with_metrics(logworks: List[Logwork]) -> Dict[str, Any]:
        """Build response payload containing logworks with status and month standards."""
        items = [LogworkService.to_dict_with_metrics(logwork) for logwork in logworks]

        standard_by_month: Dict[str, float] = {}
        for logwork in logworks:
            month_key = str(logwork.month).zfill(2)
            if month_key not in standard_by_month:
                standard_by_month[month_key] = LogworkService._get_standard_logwork_by_month(month_key)

        return {
            "standardLogworkByMonth": standard_by_month,
            "items": items,
        }
    
    @staticmethod
    def get_all() -> List[Logwork]:
        """Get all logworks"""
        return LogworkDAO.get_all()
    
    @staticmethod
    def get_by_user_id(user_id: str) -> List[Logwork]:
        """Get all logworks for a specific user"""
        return LogworkDAO.get_by_user_id(user_id)
    
    @staticmethod
    def get_by_user_id_with_month_filter(user_id: str, months: List[str] = None, quarter: str = None, year: str = None, sort_by: str = None) -> List[Logwork]:
        """Get logworks for a specific user, optionally filtered by months/quarter/year and sorted
        
        Args:
            user_id: UUID of the user
            months: Filter by list of months e.g. ['01', '03'] (optional)
            quarter: Filter by quarter 1-4 (optional)
            year: Filter by year (optional)
            sort_by: Sort by loghours ('asc' or 'desc'), default is by created date (optional)
        
        Returns:
            List of logworks for the user
        """
        if months or quarter or year or sort_by:
            return LogworkDAO.get_all_filtered(months=months, quarter=quarter, year=year, user_id=user_id, sort_by=sort_by)
        return LogworkDAO.get_by_user_id(user_id)
    
    @staticmethod
    def get_all_with_filters(months: List[str] = None, quarter: str = None, year: str = None, user_eng_name: str = None, sort_by: str = None) -> List[Logwork]:
        """Get all logworks with optional filters and sorting
        
        Args:
            months: Filter by list of months e.g. ['01', '03'] (optional)
            quarter: Filter by quarter 1-4 (optional)
            year: Filter by year (optional)
            user_eng_name: Filter by employee English name (optional)
            sort_by: Sort by loghours ('asc' or 'desc')
        
        Returns:
            List of logworks matching filters
        """
        return LogworkDAO.get_all_filtered(months=months, quarter=quarter, year=year, user_eng_name=user_eng_name, sort_by=sort_by)
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Logwork]:
        """Get logwork by UUID"""
        return LogworkDAO.get_by_id(id)
    
    @staticmethod
    def _to_dict(logwork: Logwork) -> Dict[str, Any]:
        """Convert logwork to dictionary
        
        Note: logHours is stored as Decimal in DB and returned as float in API response
        """
        return {
            "id": str(logwork.id),
            "employeeId": str(logwork.user_id),
            "logHours": float(logwork.loghours),
            "month": logwork.month,
            "year": logwork.year,
            "createdAt": logwork.created_at.isoformat() if logwork.created_at else None,
            "updatedAt": logwork.updated_at.isoformat() if logwork.updated_at else None,
            "engName": logwork.employee.en_full_name if logwork.employee else None
        }
        
    @staticmethod
    def upsert(request_data: CreateLogworkRequest) -> Tuple[Optional[Logwork], Optional[List[str]]]:
        """Create or update logwork (upsert) with validation
        
        If a logwork already exists for (user_id, month, year), update its log hours.
        Otherwise, create a new record.
        
        Args:
            request_data: CreateLogworkRequest containing user_id, log_hours, month, and year
        
        Returns:
            Tuple of (Logwork, None) if successful, or (None, errors) if failed
        """
        errors = []
        
        # Check if user exists
        user = Employee.query.filter_by(id=request_data.user_id).first()
        if not user:
            errors.append(f"User with ID '{request_data.user_id}' not found")
            return None, errors
        
        try:
            # Check if logwork already exists for this user/month/year
            existing = LogworkDAO.get_by_user_id_month_year(
                request_data.user_id, request_data.month, request_data.year
            )
            
            if existing:
                # Update existing record
                logwork = LogworkDAO.update(
                    id=str(existing.id),
                    log_hours=request_data.log_hours
                )
            else:
                # Create new record
                logwork = LogworkDAO.create(
                    user_id=request_data.user_id,
                    log_hours=request_data.log_hours,
                    month=request_data.month,
                    year=request_data.year
                )
            return logwork, None
        except Exception as e:
            return None, [f"Error upserting logwork: {str(e)}"]
    
    @staticmethod
    def update(id: str, user_id: str, request_data: UpdateLogworkRequest) -> Tuple[Optional[Logwork], Optional[List[str]]]:
        """Update logwork with validation
        
        Args:
            id: UUID of the logwork
            user_id: UUID of the current user (for authorization)
            request_data: UpdateLogworkRequest containing fields to update
        
        Returns:
            Tuple of (Logwork, None) if successful, or (None, errors) if failed
        """
        errors = []
        
        # Get logwork
        logwork = LogworkDAO.get_by_id(id)
        if not logwork:
            errors.append(f"Logwork with ID '{id}' not found")
            return None, errors
        
        try:
            # If updating month, check for duplicates
            if request_data.month:
                existing = LogworkDAO.get_by_user_id_and_month(str(logwork.user_id), request_data.month)
                year_to_check = request_data.year if request_data.year else logwork.year
                if existing and str(existing.id) != id and existing.year == year_to_check:
                    errors.append(f"Logwork already exists for this month")
                    return None, errors
            
            logwork = LogworkDAO.update(
                id=id,
                log_hours=request_data.log_hours,
                month=request_data.month,
                year=request_data.year
            )
            return logwork, None
        except Exception as e:
            return None, [f"Error updating logwork: {str(e)}"]
    
    @staticmethod
    def delete(id: str, user_id: str) -> Tuple[bool, Optional[List[str]]]:
        """Delete logwork with authorization
        
        Args:
            id: UUID of the logwork
            user_id: UUID of the current user (for authorization)
        
        Returns:
            Tuple of (True, None) if successful, or (False, errors) if failed
        """
        errors = []
        
        # Get logwork
        logwork = LogworkDAO.get_by_id(id)
        if not logwork:
            errors.append(f"Logwork with ID '{id}' not found")
            return False, errors
        
        try:
            LogworkDAO.delete(id)
            return True, None
        except Exception as e:
            return False, [f"Error deleting logwork: {str(e)}"]