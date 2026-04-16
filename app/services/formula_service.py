from typing import Optional, List, Dict, Any, Tuple, Set
from datetime import datetime
from app.dao.ticket_dao import TicketDAO
from app.dao.employee_dao import EmployeeDAO
from app.dao.formula_dao import FormulaDAO
from app.dao.ticket_type_dao import TicketTypeDAO
from app.dao.ticket_status_dao import TicketStatusDAO
from app.dao.role_dao import RoleDAO
from app.models.systemparam import SystemParameter
from app.models.ticket import Ticket
from app import db
from app.utils.math_engine import MathEngine
from app.dao.logwork_dao import LogworkDAO
from app.dao.project_dao import ProjectDAO
from app.utils.number_parser import normalize_numeric_string, parse_float_value


class FormulaService:
    """Service for managing formulas and calculating employee points"""
    
    # Known dynamic variables that are computed at runtime
    # These remain fixed in code - need new methods to add new dynamic variables
    # Format: "VARIABLE_NAME": "description"
    _PERFORMANCE_ORDER = {"Excellent": 0, "Good": 1, "Bad": 2}

    DYNAMIC_VARIABLES = {
        "TASK_COUNT": "Number of completed tasks",
        "BUG_COUNT": "Number of completed bugs",
        "LOG_HOURS": "Total log hours for employee in month/year",
        "TICKET_POINT": "Ticket contribution point",
        "LOGWORK_POINT": "Logwork contribution point",
        "MEMBER_CONTR_POINT": "Member total contribution point (ticket + logwork)",
        "TOTAL_TEAM_POINTS": "Total team contribution points",
        "BILLABLE_PARAM": "Billable parameter from system",
    }
    
    @staticmethod
    def resolve_dynamic_variable(
        variable_name: str,
        employee_id: str,
        month: int,
        year: int = None,
        total_team_points: float = None,
        ticket_point: float = None,
        logwork_point: float = None
    ) -> float:
        """Resolve dynamic variables like TASK_COUNT, LOG_HOURS, etc.
        
        Args:
            variable_name: The name of the dynamic variable (e.g., TASK_COUNT, LOG_HOURS, TICKET_POINT)
            employee_id: The employee ID
            month: The month number (1-12)
            year: The year (optional, defaults to current year)
            total_team_points: Total team contribution points (for BILLABLE_POINT_FORMULA)
            ticket_point: Pre-calculated ticket point (optional, for MEMBER_CONTR_POINT formula)
            logwork_point: Pre-calculated logwork point (optional, for MEMBER_CONTR_POINT formula)
            
        Returns:
            The computed value for the dynamic variable
        """
        variable_name = variable_name.upper()
        
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        if variable_name == "TASK_COUNT":
            return FormulaService._count_tickets(employee_id, month, "TASK")
        
        elif variable_name == "BUG_COUNT":
            return FormulaService._count_tickets(employee_id, month, "BUG")
        
        elif variable_name == "LOG_HOURS":
            return FormulaService._get_logwork_hours(employee_id, month, year)
        
        elif variable_name == "TICKET_POINT":
            # Calculate ticket point if not provided
            if ticket_point is None:
                ticket_data = FormulaService.calculate_ticket_point(employee_id, month)
                ticket_point = ticket_data.get("ticket_point", 0.0)
            return ticket_point
        
        elif variable_name == "LOGWORK_POINT":
            # Calculate logwork point if not provided
            if logwork_point is None:
                logwork_point = FormulaService.calculate_logwork_point(employee_id, month, year)
            return logwork_point
        
        elif variable_name == "MEMBER_CONTR_POINT":
            # Calculate member contribution point
            if ticket_point is None or logwork_point is None:
                ticket_data = FormulaService.calculate_ticket_point(employee_id, month)
                ticket_point = ticket_data.get("ticket_point", 0.0)
                logwork_point = FormulaService.calculate_logwork_point(employee_id, month, year)
            return FormulaService.calculate_member_contr_point(ticket_point, logwork_point, month)
        
        elif variable_name == "TOTAL_TEAM_POINTS":
            # Return pre-calculated total team points
            if total_team_points is not None:
                return total_team_points
            # Calculate if not provided
            return 0.0
        
        elif variable_name == "BILLABLE_PARAM":
            # Get BILLABLE_PARAM from system params (with month)
            billable_param = FormulaService._get_param("BILLABLE_PARAM")
            return parse_float_value(billable_param, 0.0)
        
        # Unknown dynamic variable - return 0
        return 0.0
    
    @staticmethod
    def _count_tickets(employee_id: str, month: int, ticket_type: str) -> int:
        """Count tickets of a specific type for an employee in a month"""
        from app.models.ticket import Ticket
        from app.dao.ticket_type_dao import TicketTypeDAO
        from app.dao.ticket_status_dao import TicketStatusDAO
        
        # Get ticket type
        ticket_type_obj = TicketTypeDAO.get_by_type_id(ticket_type)
        if not ticket_type_obj:
            return 0
        
        # Get closed status
        closed_status = TicketStatusDAO.get_by_status_id("CLOSED")
        if not closed_status:
            return 0
        
        # Query tickets
        count = Ticket.query.filter(
            Ticket.employee_id == employee_id,
            Ticket.month == month,
            Ticket.ticket_type_id == ticket_type_obj.id,
            Ticket.ticket_status_id == closed_status.id
        ).count()
        
        return count
    
    @staticmethod
    def _get_logwork_hours(employee_id: str, month: int, year: int = None) -> float:
        """Get logwork hours for an employee in a month (one record per employee/month/year)"""
        from app.models.logwork import Logwork
        
        # Convert month to string format (e.g., 1 -> "01")
        month_str = str(month).zfill(2)
        
        # Default to current year if not provided
        if not year:
            year = datetime.now().year

        active_non_admin_ids = {
            str(emp.id) for emp in EmployeeDAO.get_all_active_non_admin()
        }
        
        query = Logwork.query.filter(
            Logwork.user_id == employee_id,
            Logwork.month == month_str,
            Logwork.year == str(year)
        )
        
        # Get the single logwork record
        logwork = query.first()
        
        if logwork and logwork.loghours:
            return parse_float_value(logwork.loghours, 0.0)
        
        return 0.0
    
    @staticmethod
    def get_dynamic_variables() -> Dict[str, str]:
        """Get list of available dynamic variables"""
        return FormulaService.DYNAMIC_VARIABLES.copy()
    
    @staticmethod
    def _get_param(param_key: str, month: int = None) -> Optional[str]:
        """Get system parameter value by key"""
        return FormulaDAO.get_param(param_key, month)

    @staticmethod
    def get_logwork_standard_total(months: List[int]) -> float:
        """Get total STANDARD_LOGWORK from month-prefixed system params."""
        total = 0.0
        for month in months:
            value = FormulaService._get_param("STANDARD_LOGWORK", month)
            total += parse_float_value(value, 0.0)
        return total

    @staticmethod
    def get_active_employee_count() -> int:
        """Count active employees (status=True) excluding ADMIN role."""
        return EmployeeDAO.count_active_non_admin()

    @staticmethod
    def get_employee_count_with_activity(
        months: List[int],
        year: int = None,
        project_id: str = None,
    ) -> int:
        """Return max distinct member count across months from tickets or logwork activity."""
        if not months:
            return 0

        logwork_year = str(year) if year is not None else None
        monthly_counts = []

        for month in months:
            ticket_members = TicketDAO.get_distinct_employee_ids_with_tickets(
                month=month,
                project_id=project_id,
            )
            logwork_members = LogworkDAO.get_distinct_user_ids_with_logwork(
                month=str(month).zfill(2),
                year=logwork_year,
                project_id=project_id,
            )
            monthly_counts.append(len(ticket_members | logwork_members))

        return max(monthly_counts) if monthly_counts else 0

    @staticmethod
    def get_employees_total_ee() -> list:
        """Get all active non-admin employees with their total EE percent.

        totalEE = sum of allocationPercent across all project memberships.
        """
        employees = EmployeeDAO.get_all_active_non_admin()
        data = [
            {
                "enFullName": emp.en_full_name,
                "totalEE": sum((pm.allocation_percent or 0) for pm in emp.project_members),
                "projects": [
                    {
                        "projectName": pm.project.name if pm.project else None,
                        "projectId": pm.project.project_id if pm.project else None,
                        "allocationPercent": pm.allocation_percent or 0,
                    }
                    for pm in emp.project_members
                    if pm.project
                ],
            }
            for emp in employees
        ]
        data.sort(key=lambda x: x["totalEE"], reverse=True)
        return data

    @staticmethod
    def get_billable_standard_total(months: List[int]) -> float:
        """Get total billable standard across months.

        billable_standard(month) = BILLABLE_PARAM(month) / active_employee_count
        """
        active_employee_count = FormulaService.get_active_employee_count()
        if active_employee_count <= 0:
            return 0.0

        total = 0.0
        for month in months:
            billable_param = FormulaService._get_param("BILLABLE_PARAM", month)
            monthly_billable_param = parse_float_value(billable_param, 0.0)

            total += monthly_billable_param / active_employee_count

        return total

    @staticmethod
    def _get_scope_member_ee(
        project_id: str = None,
        employeeuuid: str = None,
    ) -> List[Dict[str, Any]]:
        """Get scoped members with EE percent for logwork comparison.

        - With `project_id`: EE is allocation in that project.
        - Without `project_id`: EE is total allocation across all projects.
        """
        members: Dict[str, Dict[str, Any]] = {}

        if project_id:
            project = ProjectDAO.get_by_id(project_id)
            if not project:
                return []

            for pm in project.project_members or []:
                emp = pm.employee
                if not emp or not emp.status:
                    continue
                if (emp.authorize_role or "").upper() == "ADMIN":
                    continue

                user_id = str(pm.user_id)
                if user_id not in members:
                    members[user_id] = {
                        "employee_id": user_id,
                        "employee_name": emp.en_full_name,
                        "employee_code": emp.employeeId,
                        "ee_percent": 0.0,
                    }
                members[user_id]["ee_percent"] += float(pm.allocation_percent or 0)
        else:
            employees = EmployeeDAO.get_all_active_non_admin()
            for emp in employees:
                user_id = str(emp.id)
                members[user_id] = {
                    "employee_id": user_id,
                    "employee_name": emp.en_full_name,
                    "employee_code": emp.employeeId,
                    "ee_percent": float(sum((pm.allocation_percent or 0) for pm in (emp.project_members or []))),
                }

        scoped_members = list(members.values())

        if employeeuuid:
            employeeuuid_str = str(employeeuuid)
            scoped_members = [m for m in scoped_members if m.get("employee_id") == employeeuuid_str]

        return scoped_members

    @staticmethod
    def calculate_logwork_comparison(
        months: List[int],
        year: int = None,
        project_id: str = None,
        employeeuuid: str = None,
    ) -> Dict[str, Any]:
        """Calculate expected vs actual logwork.

        For a single month, return one comparison object.
        For multiple months, keep comparison split by month in `items` and do not combine
        the month-level expected/actual values.
        """
        if not year:
            year = datetime.now().year

        if not months:
            return {
                "months": [],
                "year": year,
                "items": [],
            }

        members = FormulaService._get_scope_member_ee(project_id=project_id, employeeuuid=employeeuuid)

        def _build_month_item(month: int) -> Dict[str, Any]:
            standard_logwork_total = FormulaService.get_logwork_standard_total([month])
            month_str = str(month).zfill(2)

            member_rows: List[Dict[str, Any]] = []
            total_expected = 0.0
            total_actual = 0.0
            total_ee_percent = 0.0

            for member in members:
                employee_id = str(member.get("employee_id"))
                ee_percent = parse_float_value(member.get("ee_percent"), 0.0)
                expected = standard_logwork_total * ee_percent / 100.0
                actual = LogworkDAO.sum_hours_by_user_ids_months(
                    user_ids=[employee_id],
                    months=[month_str],
                    year=str(year),
                    project_id=project_id,
                )
                gap = actual - expected

                total_ee_percent += ee_percent
                total_expected += expected
                total_actual += actual

                member_rows.append({
                    "employee_id": employee_id,
                    "employee_name": member.get("employee_name"),
                    "employee_code": member.get("employee_code"),
                    "ee_percent": ee_percent,
                    "expected_logwork": expected,
                    "actual_logwork": actual,
                    "gap": gap,
                })

            member_rows.sort(key=lambda x: x.get("ee_percent", 0.0), reverse=True)
            achievement_percent = (total_actual / total_expected * 100.0) if total_expected > 0 else 0.0

            return {
                "month": month,
                "year": year,
                "member_count": len(member_rows),
                "standard_logwork_total": standard_logwork_total,
                "total_ee_percent": total_ee_percent,
                "expected_logwork": total_expected,
                "actual_logwork": total_actual,
                "gap": total_actual - total_expected,
                "achievement_percent": achievement_percent,
                "members": member_rows,
            }

        if len(months) == 1:
            return _build_month_item(months[0])

        return {
            "months": months,
            "year": year,
            "items": [_build_month_item(month) for month in months],
        }

    @staticmethod
    def _get_ticket_standard_by_role(role_id: str, month: int) -> Tuple[float, str]:
        """Get ticket standard value by role code for one month.

        EQA/IQA use STANDARD_QA.
        """
        role_code = (role_id or "").upper()
        if role_code in ("EQA", "IQA"):
            standard_key = "STANDARD_QA"
        else:
            standard_key = f"STANDARD_{role_code}"

        standard_value = parse_float_value(FormulaService._get_param(standard_key, month), 0.0)
        return standard_value, standard_key

    @staticmethod
    def _get_scope_member_ticket_profiles(
        month: int,
        project_id: str = None,
        employeeuuid: str = None,
    ) -> List[Dict[str, Any]]:
        """Build scoped member ticket expectation profiles for one month."""
        profiles: Dict[str, Dict[str, Any]] = {}

        def _ensure_profile(emp) -> Dict[str, Any]:
            employee_id = str(emp.id)
            if employee_id not in profiles:
                profiles[employee_id] = {
                    "employee_id": employee_id,
                    "employee_name": emp.en_full_name,
                    "employee_code": emp.employeeId,
                    "ee_percent": 0.0,
                    "expected_ticket": 0.0,
                    "role_allocations": [],
                }
            return profiles[employee_id]

        if project_id:
            project = ProjectDAO.get_by_id(project_id)
            if not project:
                return []

            for pm in project.project_members or []:
                emp = pm.employee
                if not emp or not emp.status:
                    continue
                if (emp.authorize_role or "").upper() == "ADMIN":
                    continue

                profile = _ensure_profile(emp)
                ee_percent = parse_float_value(pm.allocation_percent, 0.0)
                role_code = ((pm.role.role_id if pm.role else "") or "").upper()
                standard_value, standard_key = FormulaService._get_ticket_standard_by_role(role_code, month)
                expected_by_role = standard_value * ee_percent / 100.0

                profile["ee_percent"] += ee_percent
                profile["expected_ticket"] += expected_by_role
                profile["role_allocations"].append({
                    "role": role_code,
                    "ee_percent": ee_percent,
                    "standard_key": standard_key,
                    "standard_value": standard_value,
                    "expected_ticket": expected_by_role,
                })
        else:
            employees = EmployeeDAO.get_all_active_non_admin()

            for emp in employees:
                _ensure_profile(emp)

                for pm in emp.project_members or []:
                    ee_percent = parse_float_value(pm.allocation_percent, 0.0)
                    role_code = ((pm.role.role_id if pm.role else "") or "").upper()
                    standard_value, standard_key = FormulaService._get_ticket_standard_by_role(role_code, month)
                    expected_by_role = standard_value * ee_percent / 100.0

                    profile = profiles[str(emp.id)]
                    profile["ee_percent"] += ee_percent
                    profile["expected_ticket"] += expected_by_role
                    profile["role_allocations"].append({
                        "role": role_code,
                        "ee_percent": ee_percent,
                        "standard_key": standard_key,
                        "standard_value": standard_value,
                        "expected_ticket": expected_by_role,
                    })

        scoped_profiles = list(profiles.values())
        if employeeuuid:
            employeeuuid_str = str(employeeuuid)
            scoped_profiles = [p for p in scoped_profiles if p.get("employee_id") == employeeuuid_str]

        scoped_profiles.sort(key=lambda x: x.get("ee_percent", 0.0), reverse=True)
        return scoped_profiles

    @staticmethod
    def calculate_ticket_comparison(
        months: List[int],
        year: int = None,
        project_id: str = None,
        employeeuuid: str = None,
    ) -> Dict[str, Any]:
        """Calculate expected vs actual closed tickets.

        expected_ticket(member) = sum(role_standard(month) * role_ee_percent / 100)
        actual_ticket(member) = number of CLOSED tickets in month.
        """
        if not year:
            year = datetime.now().year

        if not months:
            return {
                "months": [],
                "year": year,
                "items": [],
            }

        def _build_month_item(month: int) -> Dict[str, Any]:
            profiles = FormulaService._get_scope_member_ticket_profiles(
                month=month,
                project_id=project_id,
                employeeuuid=employeeuuid,
            )

            members: List[Dict[str, Any]] = []
            total_expected = 0.0
            total_actual = 0.0
            total_ee_percent = 0.0

            for profile in profiles:
                employee_id = profile.get("employee_id")
                expected_ticket = parse_float_value(profile.get("expected_ticket"), 0.0)
                actual_closed_ticket = FormulaService.count_tickets(
                    month=month,
                    employeeuuid=employee_id,
                    status_id="CLOSED",
                    project_id=project_id,
                )

                total_expected += expected_ticket
                total_actual += actual_closed_ticket
                total_ee_percent += parse_float_value(profile.get("ee_percent"), 0.0)

                members.append({
                    "employee_id": employee_id,
                    "employee_name": profile.get("employee_name"),
                    "employee_code": profile.get("employee_code"),
                    "ee_percent": profile.get("ee_percent", 0.0),
                    "expected_ticket": expected_ticket,
                    "actual_closed_ticket": actual_closed_ticket,
                    "gap": actual_closed_ticket - expected_ticket,
                    "role_allocations": profile.get("role_allocations", []),
                })

            achievement_percent = (total_actual / total_expected * 100.0) if total_expected > 0 else 0.0

            return {
                "month": month,
                "year": year,
                "member_count": len(members),
                "total_ee_percent": total_ee_percent,
                "expected_ticket": total_expected,
                "actual_closed_ticket": total_actual,
                "gap": total_actual - total_expected,
                "achievement_percent": achievement_percent,
                "members": members,
            }

        if len(months) == 1:
            return _build_month_item(months[0])

        return {
            "months": months,
            "year": year,
            "items": [_build_month_item(month) for month in months],
        }
    
    @staticmethod
    def _set_param(param_key: str, param_value: str, month: int = None, description: str = None) -> SystemParameter:
        """Set system parameter value"""
        return FormulaDAO.set_param(param_key, param_value, month, description)
    
    @staticmethod
    def get_formula(month: int = None) -> Dict[str, Any]:
        """Get all formulas and all parameters
        
        Args:
            month: Month number (1-12). If provided, gets params for that month.
                  If None, defaults to current month.
        """
        # Get all formulas (keys ending with _FORMULA_STRING)
        formulas = FormulaDAO.get_formulas(month)
        
        # Get dynamic variables
        dynamic_variables = FormulaService.get_dynamic_variables()
        
        # Build list of formulas with name and value
        formula_list = []
        for formula_key, formula_value in formulas.items():
            formula_list.append({
                "name": formula_key,
                "value": formula_value or ""
            })
        
        # Get all params (keys NOT ending with _FORMULA_STRING)
        params = FormulaDAO.get_all_params(month)
        
        return {
            "formulas": formula_list,
            "parameters": params,
            "dynamic_variables": dynamic_variables
        }
    
    @staticmethod
    def update_formula(formula_string: str, formula_name: str = "TICKET_FORMULA_STRING", month: int = None) -> Dict[str, Any]:
        """Update the formula string
        
        Args:
            formula_string: The new formula string
            formula_name: The name of the formula to update (default: TICKET_FORMULA_STRING)
            month: Month number (1-12). If provided, stores with month prefix.
        """
        FormulaService._set_param(formula_name, formula_string, month, f"Formula: {formula_name}")
        return FormulaService.get_formula(month)
    
    @staticmethod
    def update_params(params: Dict[str, str], month: int = None) -> Dict[str, Any]:
        """Update formula parameters
        
        Args:
            params: Dict of param key -> value
            month: Month number (1-12). If provided, stores with month prefix.
        """
        for key, value in params.items():
            normalized_value = normalize_numeric_string(value)
            FormulaService._set_param(key, normalized_value if normalized_value is not None else str(value), month)
        
        return FormulaService.get_formula(month)
    
    @staticmethod
    def add_params(params: List[Dict[str, Any]], month: int = None) -> Dict[str, Any]:
        """Add new formula parameters or formulas
        
        Args:
            params: List of param objects, each containing:
                - param_key: The parameter/formula key to add
                - param_value: The parameter/formula value
                - description: Optional description
                - param_type: Type of item to add - "param" or "formula" (default: "param")
            month: Month number (1-12). If provided, stores with month prefix.
        
        Returns:
            Dict with all formulas and params after adding
        """
        return FormulaDAO.add_params(params, month)
    
    @staticmethod
    def add_param(param_key: str, param_value: str, description: str = None, param_type: str = "param", month: int = None) -> Dict[str, Any]:
        """Add a new formula parameter or formula (legacy single param method)
        
        Args:
            param_key: The parameter/formula key to add
            param_value: The parameter/formula value
            description: Optional description
            param_type: Type of item to add - "param" or "formula" (default: "param")
            month: Month number (1-12). If provided, stores with month prefix.
        
        Returns:
            Dict with all formulas and params after adding
        """
        # Convert single param to array format
        params = [{
            "param_key": param_key,
            "param_value": param_value,
            "description": description,
            "param_type": param_type
        }]
        return FormulaDAO.add_params(params, month)
    
    @staticmethod
    def get_role_weights_and_standard(role: str, month: int = None) -> Tuple[float, float]:
        """Get role weight and standard point for a given role
        
        Args:
            role: The role name (e.g., 'DEV', 'BA', 'QA')
            month: Month number (1-12). If provided, gets params for that month.
        """
        role = role.upper()
        
        role_weight_key = f"{role}_ROLE_WEIGHT"
        
        # Map EQA and IQA to QA for standard key lookup
        # Both EQA and IQA should use STANDARD_QA
        standard_role = "QA" if role in ("EQA", "IQA") else role
        standard_key = f"STANDARD_{standard_role}"
        
        role_weight = FormulaService._get_param(role_weight_key, month)
        standard = FormulaService._get_param(standard_key, month)
        
        # Default values if not set
        role_weight = parse_float_value(role_weight, 1.0)
        standard = parse_float_value(standard, 7.0)
        
        return role_weight, standard
    
    @staticmethod
    def calculate_ticket_point(
        employee_id: str,
        month: int,
        formula_string: str = None,
        project_id: str = None,
    ) -> Dict[str, Any]:
        """Calculate ticket point for a single employee
        
        Args:
            employee_id: The employee UUID
            month: Month number (1-12)
            formula_string: Optional custom formula (defaults to stored formula)
            project_id: Optional project UUID to filter tickets by
            
        Returns:
            Dict with ticket_point and breakdown
        """
        # Get formula - CRITICAL: validate formula_string is not None or empty
        if not formula_string:
            formula_string = FormulaService._get_param("TICKET_FORMULA_STRING", month)
        
        # CRITICAL: If still no formula, return 0 with clear reason
        if not formula_string:
            print(f"[WARNING] TICKET_FORMULA_STRING not found in database for month {month}")
            return {
                "employee_id": employee_id,
                "task_count": 0,
                "bug_count": 0,
                "ticket_point": 0.0,
                "breakdown": []
            }
        
        # Get all parameters from database
        all_params = FormulaDAO.get_all_params(month)
        
        # Build static params context (except formula strings)
        static_context = {}
        for key, value in all_params.items():
            if value and not key.endswith("_FORMULA_STRING"):
                try:
                    static_context[key] = parse_float_value(value, 0.0)
                except (ValueError, TypeError):
                    pass
        
        # Calculate point for each role and sum
        total_point = 0.0
        breakdown = []
        
        # Get employee's tickets for the month to collect roles
        closed_status_id = TicketStatusDAO.get_by_status_id("CLOSED").id
        tickets = TicketDAO.get_by_employee_month_status(
            employee_id=employee_id,
            month=month,
            ticket_status_id=closed_status_id,
            project_id=project_id,
        )
        
        # Collect all unique roles from tickets
        roles_seen = set()
        for ticket in tickets:
            if ticket.role_ids:
                for role_id in ticket.role_ids:
                    roles_seen.add(role_id)
        
        # Get ticket type IDs for counting
        bug_type = TicketTypeDAO.get_by_type_id("BUG")
        epic_type = TicketTypeDAO.get_by_type_id("EPIC")
        
        # Get role details
        from app.models.role import Role
        for role_id in roles_seen:
            role = Role.query.get(role_id)
            if not role:
                continue
            
            role_name = str(role.role_id).upper() if hasattr(role, 'role_id') else role_id
            
            # Count tickets specifically for this role
            role_task_count = 0
            role_bug_count = 0
            
            for ticket in tickets:
                # Check if this ticket has this role
                if ticket.role_ids and role_id in ticket.role_ids:
                    if ticket.ticket_type_id == bug_type.id:
                        role_bug_count += 1
                    elif ticket.ticket_type_id == epic_type.id:
                        role_task_count += 7
                    else:
                        role_task_count += 1
            
            # Get role weight and standard
            role_weight, standard = FormulaService.get_role_weights_and_standard(role_name, month)
            
            # Build context for this role - start with static params
            context = static_context.copy()
            context["ROLE_WEIGHT"] = role_weight
            context["STANDARD_ROLE"] = standard
            context["TASK_COUNT"] = role_task_count
            context["BUG_COUNT"] = role_bug_count
            
            # Calculate using MathEngine
            point = 0.0
            try:
                engine = MathEngine()
                result = engine.calculate(formula_string, context)
                point = parse_float_value(result, 0.0)
            except ZeroDivisionError as e:
                print(f"[WARNING] Division by zero in ticket_point calculation: {e}")
            except Exception as e:
                print(f"[WARNING] Error calculating ticket_point with formula '{formula_string}': {e}")
            
            total_point += point
            
            breakdown.append({
                "role": role_name,
                "role_weight": role_weight,
                "standard": standard,
                "task_count": role_task_count,
                "bug_count": role_bug_count,
                "value": point
            })
        
        # Calculate total task and bug counts (sum of all roles)
        total_task_count = sum(b["task_count"] for b in breakdown)
        total_bug_count = sum(b["bug_count"] for b in breakdown)
        
        return {
            "employee_id": employee_id,
            "task_count": total_task_count,
            "bug_count": total_bug_count,
            "ticket_point": total_point,
            "breakdown": breakdown
        }
    
    @staticmethod
    def calculate_logwork_point(
        employee_id: str,
        month: int,
        year: int = None,
        formula_string: str = None,
    ) -> float:
        """Calculate logwork point for a single employee
        
        Args:
            employee_id: The employee UUID
            month: Month number (1-12)
            year: Year (optional, defaults to current year)
            formula_string: Optional custom formula (defaults to stored formula)
            
        Returns:
            Logwork point value
        """
        # Get formula - CRITICAL: validate formula_string is not None or empty
        if not formula_string:
            formula_string = FormulaService._get_param("LOGWORK_FORMULA_STRING", month)
        
        # CRITICAL: If still no formula, return 0 with clear reason
        if not formula_string:
            print(f"[WARNING] LOGWORK_FORMULA_STRING not found in database for month {month}")
            return 0.0
        
        # Get LOG_HOURS dynamic variable
        log_hours = FormulaService._get_logwork_hours(employee_id, month, year)
        
        # Get all parameters from database
        all_params = FormulaDAO.get_all_params(month)
        
        # Build context
        context = {}
        for key, value in all_params.items():
            if value and not key.endswith("_FORMULA_STRING"):
                try:
                    context[key] = parse_float_value(value, 0.0)
                except (ValueError, TypeError):
                    pass
        
        # Add LOG_HOURS to context
        context["LOG_HOURS"] = log_hours
        
        # Calculate using MathEngine with proper error handling
        try:
            engine = MathEngine()
            result = engine.calculate(formula_string, context)
            return parse_float_value(result, 0.0)
        except ZeroDivisionError as e:
            print(f"[WARNING] Division by zero in logwork_point calculation: {e}")
            return 0.0
        except Exception as e:
            print(f"[WARNING] Error calculating logwork_point with formula '{formula_string}': {e}")
            return 0.0
    
    @staticmethod
    def calculate_member_contr_point(
        ticket_point: float,
        logwork_point: float,
        month: int,
        formula_string: str = None,
    ) -> float:
        """Calculate member contribution point
        
        Args:
            ticket_point: Ticket point from TICKET_FORMULA_STRING
            logwork_point: Logwork point from LOGWORK_FORMULA_STRING
            month: Month number (1-12)
            formula_string: Optional custom formula (defaults to stored formula)
            
        Returns:
            Member contribution point
        """
        # Get formula - CRITICAL: validate formula_string is not None or empty
        if not formula_string:
            formula_string = FormulaService._get_param("MEMBER_CONTR_POINT_FORMULA_STRING", month)
        
        # CRITICAL: If still no formula, return 0 with clear reason
        if not formula_string:
            print(f"[WARNING] MEMBER_CONTR_POINT_FORMULA_STRING not found in database for month {month}")
            # Fallback to simple addition
            return ticket_point + logwork_point
        
        # Build context with dynamic values
        context = {
            "TICKET_POINT": ticket_point,
            "LOGWORK_POINT": logwork_point,
        }
        
        # Calculate using MathEngine with proper error handling
        try:
            engine = MathEngine()
            result = engine.calculate(formula_string, context)
            return parse_float_value(result, 0.0)
        except ZeroDivisionError as e:
            print(f"[WARNING] Division by zero in member_contr_point calculation: {e}")
            # Fallback to simple addition
            return ticket_point + logwork_point
        except Exception as e:
            print(f"[WARNING] Error calculating member_contr_point with formula '{formula_string}': {e}")
            # Fallback to simple addition
            return ticket_point + logwork_point
    
    @staticmethod
    def calculate_billable_point(
        member_contr_point: float,
        total_team_points: float,
        month: int,
        formula_string: str = None,
        billable_param_override: float = None,
    ) -> float:
        """Calculate billable point
        
        Args:
            member_contr_point: Member contribution point
            total_team_points: Total team contribution points
            month: Month number (1-12)
            formula_string: Optional custom formula (defaults to stored formula)
            billable_param_override: Optional BILLABLE_PARAM override value
            
        Returns:
            Billable point
        """
        # Get formula - CRITICAL: validate formula_string is not None or empty
        if not formula_string:
            formula_string = FormulaService._get_param("BILLABLE_POINT_FORMULA_STRING", month)
        
        # CRITICAL: If still no formula, return 0 with clear reason
        if not formula_string:
            print(f"[WARNING] BILLABLE_POINT_FORMULA_STRING not found in database for month {month}")
            return 0.0
        
        # Get BILLABLE_PARAM from system params
        if billable_param_override is not None:
            billable_param_value = parse_float_value(billable_param_override, 0.0)
        else:
            billable_param = FormulaService._get_param("BILLABLE_PARAM", month)
            billable_param_value = parse_float_value(billable_param, 0.0)
        
        # Build context with dynamic values
        context = {
            "MEMBER_CONTR_POINT": member_contr_point,
            "TOTAL_TEAM_POINTS": total_team_points,
            "BILLABLE_PARAM": billable_param_value,
        }
        
        # Calculate using MathEngine with proper error handling
        try:
            engine = MathEngine()
            result = engine.calculate(formula_string, context)
            return parse_float_value(result, 0.0)
        except ZeroDivisionError as e:
            # Handle division by zero explicitly
            print(f"[WARNING] Division by zero in billable_point calculation: {e}")
            if total_team_points > 0:
                return (member_contr_point / total_team_points) * billable_param_value
            return 0.0
        except Exception as e:
            # Fallback to simple calculation if formula fails
            print(f"[WARNING] Error calculating billable_point with formula '{formula_string}': {e}")
            if total_team_points > 0:
                return (member_contr_point / total_team_points) * billable_param_value
            return 0.0
    
    @staticmethod
    def calculate_employee_all_points(
        employee_id: str,
        month: int,
        year: int = None,
        latest: bool = False,
        project_id: str = None,
    ) -> Dict[str, Any]:
        """Calculate all points for a single employee (ticket, logwork, member_contr, billable)
        
        Args:
            employee_id: The employee UUID
            month: Month number (1-12)
            year: Year (optional, defaults to current year)
            latest: If True, recalculate. If False, try to fetch from stored data.
            project_id: Optional project UUID to filter tickets by
            
        Returns:
            Dict with all point calculations
        """
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        # Check if we should fetch from stored data (only when no project filter)
        if not latest and not project_id:
            stored_data = FormulaDAO.get_calculated_data(month, year, latest=False)
            if stored_data:
                # Find this employee's data
                for emp_data in stored_data:
                    if emp_data.get("employee_id") == employee_id:
                        return emp_data
                # Employee not found in stored data, calculate fresh
        
        # 1. Calculate TICKET_POINT
        ticket_data = FormulaService.calculate_ticket_point(employee_id, month, project_id=project_id)
        ticket_point = ticket_data.get("ticket_point", 0.0)
        
        # 2. Calculate LOGWORK_POINT
        logwork_point = FormulaService.calculate_logwork_point(employee_id, month, year)
        
        # 3. Calculate MEMBER_CONTR_POINT
        member_contr_point = FormulaService.calculate_member_contr_point(ticket_point, logwork_point, month)        

        return {
            "employee_id": employee_id,
            "month": month,
            "year": year,
            "task_count": ticket_data.get("task_count", 0),
            "bug_count": ticket_data.get("bug_count", 0),
            "ticket_point": ticket_point,
            "logwork_point": logwork_point,
            "member_contr_point": member_contr_point,
            "ticket_breakdown": ticket_data.get("breakdown", []),
        }

    @staticmethod
    def _get_logwork_user_ids_by_month(month_str: str, project_id: str = None) -> Set[str]:
        """Get user IDs that have logwork records in a specific month."""
        logwork_records = LogworkDAO.get_by_month(month_str)
        if project_id:
            logwork_records = [log for log in logwork_records if str(log.project_id) == str(project_id)]
        print(f"Calculating billable metrics for month {month_str}: found {len(logwork_records)} logwork records")
        return {str(log.user_id) for log in logwork_records}

    @staticmethod
    def _get_ticket_employee_ids_by_month(month: int, project_id: str = None) -> Set[str]:
        """Get employee IDs that have any ticket in a specific month.

        If project_id is provided, only include tickets in that project.
        """
        query = Ticket.query.filter(Ticket.month == month)
        if project_id:
            query = query.filter(Ticket.project_id == project_id)

        return {
            str(ticket.employee_id)
            for ticket in query.all()
            if ticket.employee_id is not None
        }

    @staticmethod
    def _calculate_billable_metrics(
        data: List[Dict[str, Any]],
        month_str: str
    ) -> Tuple[float, float]:
        """Calculate (average_billable_point, total_billable_point) for employees with logwork in month."""
        logwork_user_ids = FormulaService._get_logwork_user_ids_by_month(month_str)

        if not logwork_user_ids:
            return 0.0, 0.0

        filtered_billable_values = [
            emp.get("billable_point", 0.0)
            for emp in data
            if str(emp.get("employee_id")) in logwork_user_ids
        ]

        if not filtered_billable_values:
            return 0.0, 0.0

        total_billable_point = sum(filtered_billable_values)
        average_billable_point = total_billable_point / len(filtered_billable_values)

        return average_billable_point, total_billable_point

    @staticmethod
    def _calculate_total_ticket_point(data: List[Dict[str, Any]]) -> float:
        """Sum ticket_point for all members in current filtered dataset."""
        return sum(emp.get("ticket_point", 0.0) for emp in data)

    @staticmethod
    def _calculate_total_logwork_point(data: List[Dict[str, Any]]) -> float:
        """Sum logwork_point for all members in current filtered dataset."""
        return sum(emp.get("logwork_point", 0.0) for emp in data)

    @staticmethod
    def count_tickets(
        month: int,
        employeeuuid: str = None,
        status_id: str = None,
        project_id: str = None,
    ) -> int:
        """Count tickets by month with optional employee, status, and project filters."""
        ticket_status_id = None
        if status_id:
            status = TicketStatusDAO.get_by_status_id(status_id)
            if not status:
                return 0
            ticket_status_id = status.id

        return TicketDAO.count_by_filters(
            month=month,
            employee_id=employeeuuid,
            ticket_status_id=ticket_status_id,
            active_only=True,
            project_id=project_id,
        )

    @staticmethod
    def get_closed_ticket_kpi(months: List[int] = None, year: int = None, project_id: str = None, ticket_type_ids: List[str] = None) -> Dict[str, Any]:
        """Get closed-ticket KPI for the given month(s) with optional project / ticket-type filter.

        Returns data for:
        - Ticket status totals (open, closed, in_qa, all)
        - Status overview breakdown (for donut chart)
        - Closed tickets by role per month (for bar + line charts)
        - Project overview table with per-role metrics
        """
        if not months:
            months = [datetime.now().month]
        if year is None:
            year = datetime.now().year

        month_strs = [str(m).zfill(2) for m in months]
        year_str = str(year)

        # --- Ticket status counts (distinct by ticket_id) ---
        all_statuses = TicketStatusDAO.get_all()
        status_uuid_map = {s.status_id: str(s.id) for s in all_statuses}

        total_tickets = TicketDAO.count_distinct_by_months_active(months, project_id=project_id, ticket_type_ids=ticket_type_ids)

        def _status_count(status_code: str) -> int:
            sid = status_uuid_map.get(status_code)
            return TicketDAO.count_distinct_by_months_active(months, ticket_status_id=sid, project_id=project_id, ticket_type_ids=ticket_type_ids) if sid else 0

        total_tickets_closed = _status_count("CLOSED")
        total_tickets_inqa = _status_count("IN_QA")
        total_tickets_open = _status_count("OPEN")

        # Status overview for donut chart
        status_overview = []
        for s in all_statuses:
            count = TicketDAO.count_distinct_by_months_active(months, ticket_status_id=str(s.id), project_id=project_id, ticket_type_ids=ticket_type_ids)
            if count > 0:
                status_overview.append({
                    "status": s.status_id,
                    "name": s.name,
                    "count": count,
                })
        status_overview.sort(key=lambda x: x["count"], reverse=True)

        # --- Closed tickets by role per month (bar + line charts) ---
        closed_status = TicketStatusDAO.get_by_status_id("CLOSED")
        eqa_role = RoleDAO.get_by_role_id("EQA")
        iqa_role = RoleDAO.get_by_role_id("IQA")
        role_map = {
            "developers_closed": RoleDAO.get_by_role_id("DEV"),
            "ba_closed": RoleDAO.get_by_role_id("BA"),
            "eqa_closed": eqa_role,
            "iqa_closed": iqa_role,
        }
        role_uuid_map = {
            key: (str(role.id) if role else None)
            for key, role in role_map.items()
        }

        role_totals = {k: 0 for k in role_uuid_map}
        total_trend: List[Dict[str, Any]] = []

        for month in months:
            month_counters = {k: 0 for k in role_uuid_map}
            distinct_closed_ids: set = set()

            if closed_status:
                closed_tickets = TicketDAO.get_by_month_status_active(
                    month=month,
                    ticket_status_id=str(closed_status.id),
                    project_id=project_id,
                    ticket_type_ids=ticket_type_ids,
                )
                for ticket in closed_tickets:
                    distinct_closed_ids.add(ticket.ticket_id)
                    ticket_role_ids = {str(rid) for rid in (ticket.role_ids or [])}
                    for key, role_uuid in role_uuid_map.items():
                        if role_uuid and role_uuid in ticket_role_ids:
                            month_counters[key] += 1

            for key in role_totals:
                role_totals[key] += month_counters[key]

            total_trend.append({
                "month": month,
                "total_closed": len(distinct_closed_ids),
            })

        # --- Project overview table ---
        if project_id:
            proj = ProjectDAO.get_by_id(project_id)
            projects = [proj] if proj else []
        else:
            projects = ProjectDAO.get_all_with_members()

        closed_status_uuid = str(closed_status.id) if closed_status else None
        project_overview = []

        for proj in projects:
            members = proj.project_members or []
            resource_allocated = len(members)

            role_groups: Dict[str, List[str]] = {}
            role_uuid_sets: Dict[str, set] = {}
            for member in members:
                role = member.role
                if not role:
                    continue
                role_key = str(role.role_id).upper()
                merged_key = "QA" if role_key in ("IQA", "EQA") else role_key
                role_groups.setdefault(merged_key, []).append(str(member.user_id))
                role_uuid_sets.setdefault(merged_key, set()).add(str(role.id))

            # For the QA group, always include both IQA and EQA role UUIDs so that
            # shadow workers logging tickets under the other QA sub-role are counted.
            if "QA" in role_uuid_sets:
                if eqa_role:
                    role_uuid_sets["QA"].add(str(eqa_role.id))
                if iqa_role:
                    role_uuid_sets["QA"].add(str(iqa_role.id))

            project_tickets_q = Ticket.query.filter(
                Ticket.project_id == str(proj.id),
                Ticket.month.in_(months),
            )
            if ticket_type_ids:
                project_tickets_q = project_tickets_q.filter(Ticket.ticket_type_id.in_(ticket_type_ids))
            project_tickets = project_tickets_q.all()

            # Discover roles from tickets that aren't represented in project members
            all_covered_uuids: set = set()
            for uuids in role_uuid_sets.values():
                all_covered_uuids |= uuids

            from app.models.role import Role as RoleModel
            for ticket in project_tickets:
                for rid in (ticket.role_ids or []):
                    rid_str = str(rid)
                    if rid_str not in all_covered_uuids:
                        role_obj = RoleModel.query.get(rid_str)
                        if role_obj:
                            rk = str(role_obj.role_id).upper()
                            mk = "QA" if rk in ("IQA", "EQA") else rk
                            role_uuid_sets.setdefault(mk, set()).add(rid_str)
                            if ticket.employee_id:
                                emp_id_str = str(ticket.employee_id)
                                if emp_id_str not in role_groups.get(mk, []):
                                    role_groups.setdefault(mk, []).append(emp_id_str)
                            all_covered_uuids.add(rid_str)

            # Ensure newly-created QA group also has both IQA and EQA UUIDs
            if "QA" in role_uuid_sets:
                if eqa_role:
                    role_uuid_sets["QA"].add(str(eqa_role.id))
                if iqa_role:
                    role_uuid_sets["QA"].add(str(iqa_role.id))

            roles_data = []
            for role_key, emp_ids in role_groups.items():
                role_uuids = role_uuid_sets.get(role_key, set())

                total_assigned = sum(
                    1 for t in project_tickets
                    if role_uuids & {str(rid) for rid in (t.role_ids or [])}
                )

                completed = 0
                if closed_status_uuid:
                    completed = sum(
                        1 for t in project_tickets
                        if role_uuids & {str(rid) for rid in (t.role_ids or [])}
                        and str(t.ticket_status_id) == closed_status_uuid
                    )

                completion = (completed / total_assigned * 100) if total_assigned > 0 else 0

                total_logged_hours = LogworkDAO.sum_hours_by_user_ids_months(
                    user_ids=emp_ids,
                    months=month_strs,
                    year=year_str,
                    project_id=str(proj.id),
                )

                efficiency = (total_logged_hours / total_assigned) if total_assigned > 0 else 0

                roles_data.append({
                    "role": role_key,
                    "total_assigned_ticket": total_assigned,
                    "completed": completed,
                    "completion": round(completion, 1),
                    "total_logged_hours": total_logged_hours,
                    "efficiency": round(efficiency, 1),
                })

            project_overview.append({
                "project_id": str(proj.id),
                "project_name": proj.name,
                "resource_allocated": resource_allocated,
                "roles": roles_data,
            })

        return {
            "months": months,
            "year": year,

            # 1) Bar chart – "Closed Tickets by Role"
            "closed_by_role_chart": {
                "months": months,
                "developers": role_totals.get("developers_closed", 0),
                "ba": role_totals.get("ba_closed", 0),
                "eqa": role_totals.get("eqa_closed", 0),
                "iqa": role_totals.get("iqa_closed", 0),
            },

            # 2) Line chart – "Total Trend"
            "total_trend_chart": {
                "months": months,
                "data": total_trend,
            },

            # 3) Donut chart – "Status Overview"
            "status_overview_chart": {
                "total_tickets": total_tickets,
                "total_tickets_open": total_tickets_open,
                "total_tickets_closed": total_tickets_closed,
                "total_tickets_inqa": total_tickets_inqa,
                "items": status_overview,
            },

            # 4) Table – "Project Overview"
            "project_overview_table": project_overview,
        }

    @staticmethod
    def filter_months_with_logwork(employee_id: str, months: List[int], year: int) -> List[int]:
        """Keep only months where the employee has logwork records for the given year."""
        months_with_logwork = []
        for m in months:
            month_str = str(m).zfill(2)
            logwork = LogworkDAO.get_by_user_id_month_year(str(employee_id), month_str, str(year))
            if logwork:
                months_with_logwork.append(m)
        return months_with_logwork
    
    @staticmethod
    def calculate_all_employees(
        month: int,
        year: int = None,
        employeeuuid: str = None,
        latest: bool = False,
        project_id: str = None,
    ) -> Tuple[List[Dict[str, Any]], float, float, float, float]:
        """Calculate all points for all employees (or filtered by employeeuuid)
        
        Args:
            month: Month number (1-12)
            year: Year (optional, defaults to current year)
            employeeuuid: Filter by employee UUID (optional)
            latest: If True, recalculate with that month's params.
                   If False, fetch from stored calculated data in DB.
            project_id: Optional project UUID to filter tickets by
            
        Returns:
            Tuple of:
            - List of employee results with all points
            - average_billable_point (only employees who have logwork in the month)
            - total_billable_point (sum of billable_point for employees who have logwork in the month)
            - total_ticket_point (sum of ticket_point based on month filter)
            - total_logwork_point (sum of logwork_point based on month filter)
        """
        month_str = str(month).zfill(2)

        # Default to current year if not provided
        if not year:
            year = datetime.now().year

        active_non_admin_ids = {
            str(emp.id) for emp in EmployeeDAO.get_all_active_non_admin()
        }
        logwork_user_ids = FormulaService._get_logwork_user_ids_by_month(month_str, project_id)
        valid_employee_ids = active_non_admin_ids | logwork_user_ids
        ticket_employee_ids = FormulaService._get_ticket_employee_ids_by_month(month, project_id)
        
        # Try to fetch from stored data if latest=False (skip when project filter is active)
        if not latest and not project_id:
            stored_data = FormulaDAO.get_calculated_data(month, year, latest=False)
            if stored_data:
                stored_data = [
                    emp for emp in stored_data
                    if str(emp.get("employee_id")) in valid_employee_ids
                ]
                # Filter by employeeuuid if provided
                if employeeuuid:
                    employeeuuid_str = str(employeeuuid)
                    filtered_data = [emp for emp in stored_data if str(emp.get("employee_id")) == employeeuuid_str]
                    average_billable_point, total_billable_point = FormulaService._calculate_billable_metrics(filtered_data, month_str)
                    total_ticket_point = FormulaService._calculate_total_ticket_point(filtered_data)
                    total_logwork_point = FormulaService._calculate_total_logwork_point(filtered_data)
                    # Use full stored_data (whole team) for average_ee, not just the filtered employee
                    average_ee = FormulaService.calculate_average_team_ee(stored_data, month)
                    return filtered_data, average_billable_point, total_billable_point, total_ticket_point, total_logwork_point, average_ee
                average_billable_point, total_billable_point = FormulaService._calculate_billable_metrics(stored_data, month_str)
                total_ticket_point = FormulaService._calculate_total_ticket_point(stored_data)
                total_logwork_point = FormulaService._calculate_total_logwork_point(stored_data)
                average_ee = FormulaService.calculate_average_team_ee(stored_data, month)
                stored_data = [
                    emp for emp in stored_data
                    if emp.get("ticket_point", 0) != 0
                    or emp.get("logwork_point", 0) != 0
                ]
                stored_data.sort(key=lambda x: (
                    FormulaService._PERFORMANCE_ORDER.get(
                        x.get("member_performance", {}).get("performance_level", "Bad"), 99
                    ),
                    -x.get("ticket_point", 0)
                ))
                return stored_data, average_billable_point, total_billable_point, total_ticket_point, total_logwork_point, average_ee
        
        # Need to calculate fresh
        # Always compute with full team context so billable distribution is consistent.
        # Include inactive employees who still have logwork data for this month.
        employees = list(EmployeeDAO.get_all_active_non_admin())
        active_ids = {str(emp.id) for emp in employees}
        for uid in logwork_user_ids - active_ids:
            emp = EmployeeDAO.get_by_id(uid)
            if emp and (emp.authorize_role or "").upper() != "ADMIN":
                employees.append(emp)
        
        results = []
        total_team_points = 0.0
        
        # First pass: calculate ticket_point, logwork_point, member_contr_point for each employee
        for employee in employees:
            # Get employee details
            employee_data = {
                "id": str(employee.id),
                "employee_id": employee.employeeId,
                "en_full_name": employee.en_full_name,
                "vn_full_name": employee.vn_full_name,
                "email": employee.email,
            }
            
            # Calculate all points using global data (project_id only filters which
            # employees appear in results, it must not affect individual calculations)
            point_data = FormulaService.calculate_employee_all_points(
                employee_id=str(employee.id),
                month=month,
                year=year,
                latest=True,
            )
            
            # Add employee info
            point_data["employee"] = employee_data
            
            # Accumulate total team points
            total_team_points += point_data["member_contr_point"]
            
            results.append(point_data)

        # Split BILLABLE_PARAM: 90% for shared formula, 10% evenly for manager users.
        billable_param = FormulaService._get_param("BILLABLE_PARAM", month)
        billable_param_value = parse_float_value(billable_param, 0.0)
        common_billable_param = billable_param_value * 0.9
        manager_bonus_pool = billable_param_value * 0.1

        manager_employee_ids = {
            str(emp.id)
            for emp in employees
            if (getattr(emp, "authorize_role", "") or "").upper() == "MANAGER"
        }
        manager_bonus_per_employee = (
            manager_bonus_pool / len(manager_employee_ids)
            if manager_employee_ids else 0.0
        )
        
        # Second pass: calculate billable point for each employee
        for result in results:
            billable_point = FormulaService.calculate_billable_point(
                member_contr_point=result["member_contr_point"],
                total_team_points=total_team_points,
                month=month,
                billable_param_override=common_billable_param,
            )

            if str(result.get("employee_id")) in manager_employee_ids:
                billable_point += manager_bonus_per_employee

            result["total_team_points"] = total_team_points
            result["billable_point"] = billable_point

            employee_id = result.get("employee_id")

            result["member_performance"] = FormulaService.calculate_member_performance(employee_id, billable_point, month)
        
        average_ee = FormulaService.calculate_average_team_ee(results, month)

        # Compute global aggregate metrics BEFORE any filtering
        average_billable_point, total_billable_point = FormulaService._calculate_billable_metrics(results, month_str)
        total_ticket_point = FormulaService._calculate_total_ticket_point(results)
        total_logwork_point = FormulaService._calculate_total_logwork_point(results)

        # Save to DB before filtering (full team data)
        if latest and not project_id:
            FormulaDAO.save_calculated_data(month, year, results)

        if employeeuuid:
            employeeuuid_str = str(employeeuuid)
            results = [emp for emp in results if str(emp.get("employee_id")) == employeeuuid_str]

        # Filter out employees where both ticket_point and logwork_point are 0
        if project_id:
            results = [emp for emp in results if str(emp.get("employee_id")) in ticket_employee_ids
                       or str(emp.get("employee_id")) in logwork_user_ids]
        
        if not employeeuuid:
            results = [emp for emp in results
                       if emp.get("ticket_point", 0) != 0
                       or emp.get("logwork_point", 0) != 0]

        results.sort(key=lambda x: (
            FormulaService._PERFORMANCE_ORDER.get(
                x.get("member_performance", {}).get("performance_level", "Bad"), 99
            ),
            -x.get("ticket_point", 0)
        ))

        return results, average_billable_point, total_billable_point, total_ticket_point, total_logwork_point, average_ee
    
    @staticmethod
    def calculate_total_ee(employee_id: str) -> int:
        """Calculate total EE (Estimated Effort) for an employee across all projects
        
        Args:
            employee_id: The employee UUID
            
        Returns:
            Total allocation percent summed across all projects
            Example: 50% in Project A + 40% in Project B = 90%
        """
        # Get all project memberships for this employee (across all projects)
        memberships = ProjectDAO.get_all_memberships_by_user(employee_id)
        
        # Calculate total EE (sum of allocation_percent across all projects)
        total_ee = sum(membership.allocation_percent for membership in memberships)
        
        return total_ee

    @staticmethod
    def _get_performance_level(performance_result: float, month_count: int = 1) -> str:
        """Map performance result to level with thresholds scaled by month_count.

        Base thresholds for 1 month:
        - < 1: Bad
        - >= 1 and < 2: Good
        - >= 2: Excellent

        For N months, thresholds become:
        - < N: Bad
        - >= N and < 2N: Good
        - >= 2N: Excellent
        """
        safe_month_count = month_count if month_count and month_count > 0 else 1
        good_threshold = float(safe_month_count)
        excellent_threshold = float(2 * safe_month_count)

        if performance_result >= excellent_threshold:
            return "Excellent"
        if performance_result >= good_threshold:
            return "Good"
        return "Bad"

    @staticmethod
    def build_member_performance(total_ee: float, performance_result: float, month_count: int = 1) -> Dict[str, Any]:
        """Build member_performance payload using scalable thresholds."""
        return {
            "performance_level": FormulaService._get_performance_level(performance_result, month_count),
            "total_ee": total_ee,
            "performance_result": performance_result,
        }
    
    # Calculate member performance level based on billable point and predefined thresholds (optional enhancement)
    @staticmethod
    def calculate_member_performance(
        employee_id: str,
        billable_point: float,
        month: int,
        month_count: int = 1,
    ) -> Dict[str, Any]:
        """Calculate member performance level based on billable point and thresholds
        
        Args:
            employee_id: The employee UUID
            billable_point: The calculated billable point for the employee
            month: Month number (1-12) to get thresholds for
            
        Returns:
            Dict with performance level and total_ee
        """
        # Get number of employees with logwork in that month (convert month to 2-digit string)
        month_str = str(month).zfill(2)
        member_count = len(FormulaService._get_logwork_user_ids_by_month(month_str))
        
        # Get billable param for the month
        billable_param = FormulaService._get_param("BILLABLE_PARAM", month)
        print(f"Calculating performance for employee {employee_id} in month {month_str}: billable_point={billable_point}, member_count={member_count}, billable_param={billable_param}")
        billable_param_value = parse_float_value(billable_param, 0.0)
        
        # Calculate performance point: billable_point / (billable_param/member_count)
        if member_count > 0 and billable_param_value > 0:
            performance_point = billable_point / (billable_param_value / member_count)
        else:
            performance_point = 0.0
        
        # Calculate total EE using the dedicated function
        total_ee = FormulaService.calculate_total_ee(employee_id)
        
        print(f"Employee {employee_id}: performance_point={performance_point}, total_ee={total_ee}%, member_count={member_count}")

        # Calculate final result: performance_point / total_ee
        if total_ee > 0:
            result = 100 * performance_point / total_ee
        else:
            # If no allocation, default to "Bad"
            result = 0.0
        
        performance_level = FormulaService._get_performance_level(result, month_count)

        print(f"Employee {employee_id}: final performance result={result}, level={performance_level}")
        return FormulaService.build_member_performance(total_ee, result, month_count)

    # Keep legacy method for backward compatibility
    @staticmethod
    def calculate_employee_point(
        employee_id: str,
        month: int,
        formula_string: str = None,
    ) -> Dict[str, Any]:
        """Calculate point for a single employee (legacy method)
        
        Args:
            employee_id: The employee UUID
            month: Month number (1-12)
            formula_string: Optional custom formula (defaults to stored formula)
            
        Returns:
            Dict with point calculation
        """
        return FormulaService.calculate_ticket_point(employee_id, month, formula_string)
    
    @staticmethod
    def calculate_average_team_ee(team_results: list, month: int):
        total_team_ee = 0.0
        for r in team_results:
            # total_ee is stored as percentage (e.g. 100, 60, 20), convert to decimal before summing
            total_team_ee += r.get("member_performance", {}).get("total_ee", 0.0) / 100

        if total_team_ee <= 0:
            return 0.0

        billable_param = FormulaService._get_param("BILLABLE_PARAM", month)
        billable_param_value = parse_float_value(billable_param, 0.0)

        average_ee = billable_param_value / total_team_ee * 100
        return average_ee