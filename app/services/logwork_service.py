from typing import Optional, List, Dict, Any, Tuple
from app.dao.logwork_dao import LogworkDAO
from app.dao.formula_dao import FormulaDAO
from app.dao.project_dao import ProjectDAO
from app.models.logwork import Logwork
from app.models.employee import Employee
from app.requests.logwork_request import CreateLogworkRequest, UpdateLogworkRequest
from app.utils.number_parser import parse_float_value


class LogworkService:

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        return parse_float_value(value, default)

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
    def _build_metrics_for_values(user_id: str, month: str, log_hours: float) -> Dict[str, Any]:
        """Build status and estimate metrics from normalized values."""
        standard_logwork = LogworkService._get_standard_logwork_by_month(month)
        total_ee_percent = LogworkService._get_total_ee_percent_by_user(user_id)
        ee_ratio = total_ee_percent / 100.0

        estimate_score = 0.0
        denominator = standard_logwork * ee_ratio
        if denominator > 0:
            estimate_score = float(log_hours) / denominator

        return {
            "standardLogworkInMonth": standard_logwork,
            "totalEEPercent": total_ee_percent,
            "estimateScore": round(estimate_score, 4),
            "status": 1 if estimate_score >= 1 else 0,
        }

    @staticmethod
    def _build_metrics(logwork: Logwork) -> Dict[str, Any]:
        """Build status and estimate metrics for a logwork row."""
        return LogworkService._build_metrics_for_values(
            user_id=str(logwork.user_id),
            month=logwork.month,
            log_hours=float(logwork.loghours),
        )

    @staticmethod
    def to_dict_with_metrics(logwork: Logwork) -> Dict[str, Any]:
        """Convert a logwork object to response dict with estimate metrics."""
        data = LogworkService._to_dict(logwork)
        data.update(LogworkService._build_metrics(logwork))
        return data

    @staticmethod
    def to_list_with_metrics(logworks: List[Logwork]) -> Dict[str, Any]:
        """Build grouped payload by employee with detailed rows and monthly totals."""
        grouped: Dict[str, Dict[str, Any]] = {}

        for logwork in logworks:
            employee_id = str(logwork.user_id)
            row = LogworkService.to_dict_with_metrics(logwork)

            if employee_id not in grouped:
                grouped[employee_id] = {
                    "createdAt": row.get("createdAt"),
                    "employeeId": employee_id,
                    "engName": row.get("engName"),
                    "data": [],
                }

            employee_group = grouped[employee_id]
            created_at = row.get("createdAt")
            if created_at and (employee_group.get("createdAt") is None or created_at < employee_group["createdAt"]):
                employee_group["createdAt"] = created_at

            employee_group["data"].append(row)

        result: List[Dict[str, Any]] = []
        for employee in grouped.values():
            total_by_month_year: Dict[Tuple[str, str], Dict[str, Any]] = {}
            for item in employee["data"]:
                month = item.get("month")
                year = item.get("year")
                key = (month, year)
                if key not in total_by_month_year:
                    total_by_month_year[key] = {
                        "month": month,
                        "year": year,
                        "totalLoghour": 0.0,
                    }
                total_by_month_year[key]["totalLoghour"] += float(item.get("logHours", 0.0))

            totals: List[Dict[str, Any]] = []
            for total in total_by_month_year.values():
                metrics = LogworkService._build_metrics_for_values(
                    user_id=employee["employeeId"],
                    month=total["month"],
                    log_hours=total["totalLoghour"],
                )
                totals.append(
                    {
                        "month": total["month"],
                        "year": total["year"],
                        "totalLoghour": round(total["totalLoghour"], 2),
                        "standardLogworkInMonth": metrics["standardLogworkInMonth"],
                        "estimateScore": metrics["estimateScore"],
                        "status": metrics["status"],
                    }
                )

            employee["data"].sort(
                key=lambda item: (item.get("year") or "", item.get("month") or "", item.get("createdAt") or ""),
                reverse=True,
            )
            employee["total"] = sorted(
                totals,
                key=lambda item: (item.get("year") or "", item.get("month") or ""),
                reverse=True,
            )
            result.append(employee)

        result.sort(
            key=lambda item: ((item.get("engName") or ""), (item.get("employeeId") or "")),
        )
        return {"items": result}

    @staticmethod
    def to_member_payload(logworks: List[Logwork], user_id: str, eng_name: str) -> Dict[str, Any]:
        """Build single-member payload for member endpoint."""
        payload = LogworkService.to_list_with_metrics(logworks)
        items = payload.get("items", [])
        if items:
            return items[0]

        return {
            "createdAt": None,
            "employeeId": user_id,
            "engName": eng_name,
            "data": [],
            "total": [],
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
    def get_by_user_id_with_month_filter(
        user_id: str,
        months: List[str] = None,
        quarter: str = None,
        year: str = None,
        project_id: str = None,
        sort_by: str = None,
    ) -> List[Logwork]:
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
        if months or quarter or year or project_id or sort_by:
            return LogworkDAO.get_all_filtered(
                months=months,
                quarter=quarter,
                year=year,
                user_id=user_id,
                project_id=project_id,
                sort_by=sort_by,
            )
        return LogworkDAO.get_by_user_id(user_id)
    
    @staticmethod
    def get_all_with_filters(
        months: List[str] = None,
        quarter: str = None,
        year: str = None,
        user_eng_name: str = None,
        project_id: str = None,
        sort_by: str = None,
    ) -> List[Logwork]:
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
        return LogworkDAO.get_all_filtered(
            months=months,
            quarter=quarter,
            year=year,
            user_eng_name=user_eng_name,
            project_id=project_id,
            sort_by=sort_by,
        )
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Logwork]:
        """Get logwork by UUID"""
        return LogworkDAO.get_by_id(id)
    
    @staticmethod
    def _get_project_ee_info(user_id: str, project_id: str) -> list:
        """Return [{projectId, projectName, projectKey, EEPercent}] for a single project_id."""
        if not project_id:
            return []
        memberships = ProjectDAO.get_all_memberships_by_user(user_id)
        membership_map = {str(pm.project_id): pm for pm in memberships}
        pm = membership_map.get(str(project_id))
        return [{
            "projectId": str(project_id),
            "projectName": pm.project.name if pm and pm.project else None,
            "projectKey": pm.project.project_id if pm and pm.project else None,
            "EEPercent": pm.allocation_percent if pm else None,
        }]

    @staticmethod
    def _to_dict(logwork: Logwork) -> Dict[str, Any]:
        """Convert logwork to dictionary.

        Returns per-project EE info (from project_members) and totalEEPercent.
        """
        user_id = str(logwork.user_id)
        project_id = str(logwork.project_id) if logwork.project_id else None
        projects = LogworkService._get_project_ee_info(user_id, project_id)
        total_ee = sum(p["EEPercent"] for p in projects if p["EEPercent"] is not None)
        return {
            "id": str(logwork.id),
            "employeeId": user_id,
            "engName": logwork.employee.en_full_name if logwork.employee else None,
            "logHours": float(logwork.loghours),
            "month": logwork.month,
            "year": logwork.year,
            "projects": projects,
            "totalEEPercent": total_ee,
            "createdAt": logwork.created_at.isoformat() if logwork.created_at else None,
            "updatedAt": logwork.updated_at.isoformat() if logwork.updated_at else None,
        }
        
    @staticmethod
    def upsert(request_data: CreateLogworkRequest) -> Tuple[Optional[Logwork], Optional[List[str]], bool]:
        """Create, update, or delete logwork keyed on (user_id, project_id, month, year).

        A logHour value of 0 removes the matching record instead of saving a zero-hour row.
        """
        errors = []

        user = Employee.query.filter_by(id=request_data.user_id).first()
        if not user:
            errors.append(f"User with ID '{request_data.user_id}' not found")
            return None, errors, False

        try:
            existing = LogworkDAO.get_by_user_id_month_year(
                request_data.user_id,
                request_data.month,
                request_data.year,
                request_data.project_id,
            )

            if request_data.log_hours == 0:
                if existing:
                    LogworkDAO.delete(str(existing.id))
                return None, None, True

            if existing:
                logwork = LogworkDAO.update(
                    id=str(existing.id),
                    project_id=request_data.project_id,
                    log_hours=request_data.log_hours,
                )
            else:
                logwork = LogworkDAO.create(
                    user_id=request_data.user_id,
                    project_id=request_data.project_id,
                    log_hours=request_data.log_hours,
                    month=request_data.month,
                    year=request_data.year,
                )
            return logwork, None, False
        except Exception as e:
            return None, [f"Error upserting logwork: {str(e)}"], False
    
    @staticmethod
    def update(id: str, user_id: str, request_data: UpdateLogworkRequest) -> Tuple[Optional[Logwork], Optional[List[str]]]:
        """Update logwork fields."""
        errors = []

        logwork = LogworkDAO.get_by_id(id)
        if not logwork:
            errors.append(f"Logwork with ID '{id}' not found")
            return None, errors

        try:
            month_to_check = request_data.month if request_data.month else logwork.month
            year_to_check = request_data.year if request_data.year else logwork.year

            project_id_to_check = request_data.project_id if request_data.project_id else str(logwork.project_id)

            # Ensure no duplicate row for (user_id, project_id, month, year)
            if request_data.month or request_data.year or request_data.project_id:
                existing = LogworkDAO.get_by_user_id_month_year(
                    str(logwork.user_id),
                    month_to_check,
                    year_to_check,
                    project_id_to_check,
                )
                if existing and str(existing.id) != id:
                    errors.append("Logwork already exists for this user, project, month, and year")
                    return None, errors

            logwork = LogworkDAO.update(
                id=id,
                project_id=request_data.project_id,
                log_hours=request_data.log_hours,
                month=request_data.month,
                year=request_data.year,
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