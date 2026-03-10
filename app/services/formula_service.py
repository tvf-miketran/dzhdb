from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from app.dao.ticket_dao import TicketDAO
from app.dao.employee_dao import EmployeeDAO
from app.dao.formula_dao import FormulaDAO
from app.dao.ticket_type_dao import TicketTypeDAO
from app.dao.ticket_status_dao import TicketStatusDAO
from app.models.systemparam import SystemParameter
from app.models.ticket import Ticket
from app.models.employee import Employee
from app import db
from app.utils.math_engine import MathEngine


class FormulaService:
    """Service for managing formulas and calculating employee points"""
    
    # Default formula string
    DEFAULT_TICKET_FORMULA = "(TASK_COUNT * TASK_WEIGHT + BUG_COUNT * BUG_WEIGHT) * ROLE_WEIGHT / STANDARD_ROLE"
    DEFAULT_LOGWORK_FORMULA = "LOG_HOURS / STANDARD_LOGWORK"
    DEFAULT_MEMBER_CONTR_FORMULA = "TICKET_POINT + LOGWORK_POINT"
    DEFAULT_BILLABLE_FORMULA = "MEMBER_CONTR_POINT / TOTAL_TEAM_POINTS * BILLABLE_PARAM"
    
    # Known dynamic variables that are computed at runtime
    # Format: "VARIABLE_NAME": "description"
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
            return FormulaService.calculate_member_contr_point(ticket_point, logwork_point)
        
        elif variable_name == "TOTAL_TEAM_POINTS":
            # Return pre-calculated total team points
            if total_team_points is not None:
                return total_team_points
            # Calculate if not provided
            return 0.0
        
        elif variable_name == "BILLABLE_PARAM":
            # Get BILLABLE_PARAM from system params
            billable_param = FormulaService._get_param("BILLABLE_PARAM")
            return float(billable_param) if billable_param else 0.0
        
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
        
        query = Logwork.query.filter(
            Logwork.user_id == employee_id,
            Logwork.month == month_str,
            Logwork.year == str(year)
        )
        
        # Get the single logwork record
        logwork = query.first()
        
        if logwork and logwork.loghours:
            return float(logwork.loghours)
        
        return 0.0
    
    @staticmethod
    def get_dynamic_variables() -> Dict[str, str]:
        """Get list of available dynamic variables"""
        return FormulaService.DYNAMIC_VARIABLES.copy()
    
    @staticmethod
    def _get_param(param_key: str) -> Optional[str]:
        """Get system parameter value by key"""
        return FormulaDAO.get_param(param_key)
    
    @staticmethod
    def _set_param(param_key: str, param_value: str, description: str = None) -> SystemParameter:
        """Set system parameter value"""
        return FormulaDAO.set_param(param_key, param_value, description)
    
    @staticmethod
    def get_formula() -> Dict[str, Any]:
        """Get all formulas and all parameters"""
        # Get all formula name keys
        formula_name_keys = FormulaDAO.get_formula_name_keys()
        
        # Get required params mapping
        required_params_mapping = FormulaDAO.get_formula_required_params()
        
        # Get dynamic variables
        dynamic_variables = FormulaService.get_dynamic_variables()
        
        # Build list of formulas with name, value, and required_params
        formulas = []
        for formula_key in formula_name_keys:
            formula_value = FormulaService._get_param(formula_key)
            formulas.append({
                "name": formula_key,
                "value": formula_value or "",
                "required_params": required_params_mapping.get(formula_key, [])
            })
        
        # Get all params and filter out formula strings (they're already in formulas)
        all_params = FormulaDAO.get_all_params()
        params = {}
        for key, value in all_params.items():
            if not key.endswith("_FORMULA_STRING"):
                params[key] = value
        
        return {
            "formulas": formulas,
            "parameters": params,
            "dynamic_variables": dynamic_variables
        }
    
    @staticmethod
    def update_formula(formula_string: str, formula_name: str = "TICKET_FORMULA_STRING") -> Dict[str, Any]:
        """Update the formula string
        
        Args:
            formula_string: The new formula string
            formula_name: The name of the formula to update (default: TICKET_FORMULA_STRING)
        """
        FormulaService._set_param(formula_name, formula_string, f"Formula: {formula_name}")
        return FormulaService.get_formula()
    
    @staticmethod
    def update_params(params: Dict[str, str]) -> Dict[str, Any]:
        """Update formula parameters"""
        param_keys = FormulaDAO.get_param_keys()
        for key, value in params.items():
            if key in param_keys:
                FormulaService._set_param(key, str(value))
        
        return FormulaService.get_formula()
    
    @staticmethod
    def add_param(param_key: str, param_value: str, description: str = None, param_type: str = "param", required_params: List[str] = None) -> Dict[str, Any]:
        """Add a new formula parameter or formula
        
        Args:
            param_key: The parameter/formula key to add
            param_value: The parameter/formula value
            description: Optional description
            param_type: Type of item to add - "param" or "formula" (default: "param")
            required_params: List of parameter keys this formula requires (only for type="formula")
        
        Returns:
            Dict with all formulas and params after adding
        """
        return FormulaDAO.add_param(param_key, param_value, description, param_type, required_params)
    
    @staticmethod
    def get_role_weights_and_standard(role: str) -> Tuple[float, float]:
        """Get role weight and standard point for a given role"""
        role = role.upper()
        
        role_weight_key = f"{role}_ROLE_WEIGHT"
        
        # Map EQA and IQA to QA for standard key lookup
        # Both EQA and IQA should use STANDARD_QA
        standard_role = "QA" if role in ("EQA", "IQA") else role
        standard_key = f"STANDARD_{standard_role}"
        
        role_weight = FormulaService._get_param(role_weight_key)
        standard = FormulaService._get_param(standard_key)
        
        # Default values if not set
        role_weight = float(role_weight) if role_weight else 1.0
        standard = float(standard) if standard else 7.0
        
        return role_weight, standard
    
    @staticmethod
    def calculate_ticket_point(
        employee_id: str,
        month: int,
        formula_string: str = None,
    ) -> Dict[str, Any]:
        """Calculate ticket point for a single employee
        
        Args:
            employee_id: The employee UUID
            month: Month number (1-12)
            formula_string: Optional custom formula (defaults to stored formula)
            
        Returns:
            Dict with ticket_point and breakdown
        """
        # Get formula
        if not formula_string:
            formula_string = FormulaService._get_param("TICKET_FORMULA_STRING") or FormulaService.DEFAULT_TICKET_FORMULA
        
        # Get all parameters from database
        all_params = FormulaDAO.get_all_params()
        
        # Build static params context (except formula strings)
        static_context = {}
        for key, value in all_params.items():
            if value and not key.endswith("_FORMULA_STRING"):
                try:
                    static_context[key] = float(value)
                except (ValueError, TypeError):
                    pass
        
        # Calculate point for each role and sum
        total_point = 0.0
        breakdown = []
        
        # Get employee's tickets for the month to collect roles
        tickets = Ticket.query.filter(
            Ticket.employee_id == employee_id,
            Ticket.month == month
        ).all()
        
        # Collect all unique roles from tickets
        roles_seen = set()
        for ticket in tickets:
            if ticket.role_ids:
                for role_id in ticket.role_ids:
                    roles_seen.add(role_id)
        
        # Get ticket type IDs for counting
        task_type = TicketTypeDAO.get_by_type_id("TASK")
        bug_type = TicketTypeDAO.get_by_type_id("BUG")
        
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
                    elif ticket.ticket_type_id == task_type.id:
                        role_task_count += 1
            
            # Get role weight and standard
            role_weight, standard = FormulaService.get_role_weights_and_standard(role_name)
            
            # Build context for this role - start with static params
            context = static_context.copy()
            context["ROLE_WEIGHT"] = role_weight
            context["STANDARD_ROLE"] = standard
            context["TASK_COUNT"] = role_task_count
            context["BUG_COUNT"] = role_bug_count
            
            # Calculate using MathEngine
            try:
                engine = MathEngine()
                result = engine.calculate(formula_string, context)
                point = float(result)
            except Exception as e:
                point = 0.0
            
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
        # Get formula
        if not formula_string:
            formula_string = FormulaService._get_param("LOGWORK_FORMULA_STRING") or FormulaService.DEFAULT_LOGWORK_FORMULA
        
        # Get LOG_HOURS dynamic variable
        log_hours = FormulaService._get_logwork_hours(employee_id, month, year)
        
        # Get all parameters from database
        all_params = FormulaDAO.get_all_params()
        
        # Build context
        context = {}
        for key, value in all_params.items():
            if value and not key.endswith("_FORMULA_STRING"):
                try:
                    context[key] = float(value)
                except (ValueError, TypeError):
                    pass
        
        # Add LOG_HOURS to context
        context["LOG_HOURS"] = log_hours
        
        # Calculate using MathEngine
        try:
            engine = MathEngine()
            result = engine.calculate(formula_string, context)
            return float(result)
        except Exception as e:
            return 0.0
    
    @staticmethod
    def calculate_member_contr_point(
        ticket_point: float,
        logwork_point: float,
        formula_string: str = None,
    ) -> float:
        """Calculate member contribution point
        
        Args:
            ticket_point: Ticket point from TICKET_FORMULA_STRING
            logwork_point: Logwork point from LOGWORK_FORMULA_STRING
            formula_string: Optional custom formula (defaults to stored formula)
            
        Returns:
            Member contribution point
        """
        # Get formula
        if not formula_string:
            formula_string = FormulaService._get_param("MEMBER_CONTR_POINT_FORMULA_STRING") or FormulaService.DEFAULT_MEMBER_CONTR_FORMULA
        
        # Build context with dynamic values
        context = {
            "TICKET_POINT": ticket_point,
            "LOGWORK_POINT": logwork_point,
        }
        
        # Calculate using MathEngine
        try:
            engine = MathEngine()
            result = engine.calculate(formula_string, context)
            return float(result)
        except Exception as e:
            # Fallback to simple addition if formula fails
            return ticket_point + logwork_point
    
    @staticmethod
    def calculate_billable_point(
        member_contr_point: float,
        total_team_points: float,
        formula_string: str = None,
    ) -> float:
        """Calculate billable point
        
        Args:
            member_contr_point: Member contribution point
            total_team_points: Total team contribution points
            formula_string: Optional custom formula (defaults to stored formula)
            
        Returns:
            Billable point
        """
        # Get formula
        if not formula_string:
            formula_string = FormulaService._get_param("BILLABLE_POINT_FORMULA_STRING") or FormulaService.DEFAULT_BILLABLE_FORMULA
        
        # Get BILLABLE_PARAM from system params
        billable_param = FormulaService._get_param("BILLABLE_PARAM")
        billable_param_value = float(billable_param) if billable_param else 0.0
        
        # Build context with dynamic values
        context = {
            "MEMBER_CONTR_POINT": member_contr_point,
            "TOTAL_TEAM_POINTS": total_team_points,
            "BILLABLE_PARAM": billable_param_value,
        }
        
        # Calculate using MathEngine
        try:
            engine = MathEngine()
            result = engine.calculate(formula_string, context)
            return float(result)
        except Exception as e:
            # Fallback to simple calculation if formula fails
            if total_team_points > 0:
                return (member_contr_point / total_team_points) * billable_param_value
            return 0.0
    
    @staticmethod
    def calculate_employee_all_points(
        employee_id: str,
        month: int,
        year: int = None,
    ) -> Dict[str, Any]:
        """Calculate all points for a single employee (ticket, logwork, member_contr, billable)
        
        Args:
            employee_id: The employee UUID
            month: Month number (1-12)
            year: Year (optional, defaults to current year)
            
        Returns:
            Dict with all point calculations
        """
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        # 1. Calculate TICKET_POINT
        ticket_data = FormulaService.calculate_ticket_point(employee_id, month)
        ticket_point = ticket_data.get("ticket_point", 0.0)
        
        # 2. Calculate LOGWORK_POINT
        logwork_point = FormulaService.calculate_logwork_point(employee_id, month, year)
        
        # 3. Calculate MEMBER_CONTR_POINT
        member_contr_point = FormulaService.calculate_member_contr_point(ticket_point, logwork_point)
        
        # Return all points (billable will be calculated in calculate_all_employees after getting total team points)
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
    def calculate_all_employees(
        month: int,
        year: int = None,
        employeeuuid: str = None,
    ) -> List[Dict[str, Any]]:
        """Calculate all points for all employees (or filtered by employeeuuid)
        
        Args:
            month: Month number (1-12)
            year: Year (optional, defaults to current year)
            employeeuuid: Filter by employee UUID (optional)
            
        Returns:
            List of employee results with all points
        """
        # Default to current year if not provided
        if not year:
            year = datetime.now().year
        
        # Query employees
        if employeeuuid:
            employees = Employee.query.filter_by(id=employeeuuid).all()
        else:
            employees = Employee.query.all()
        
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
            
            # Calculate all points
            point_data = FormulaService.calculate_employee_all_points(
                employee_id=str(employee.id),
                month=month,
                year=year
            )
            
            # Add employee info
            point_data["employee"] = employee_data
            
            # Accumulate total team points
            total_team_points += point_data["member_contr_point"]
            
            results.append(point_data)
        
        # Second pass: calculate billable point for each employee
        for result in results:
            billable_point = FormulaService.calculate_billable_point(
                member_contr_point=result["member_contr_point"],
                total_team_points=total_team_points
            )
            result["total_team_points"] = total_team_points
            result["billable_point"] = billable_point
        
        # Sort by ticket_point descending
        results.sort(key=lambda x: x["ticket_point"], reverse=True)
        
        return results
    
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
    
    # Keep legacy method for backward compatibility
    @staticmethod
    def calculate_all_employees_legacy(
        month: int,
        formula_string: str = None
    ) -> List[Dict[str, Any]]:
        """Calculate points for all employees (legacy method)"""
        employees = Employee.query.all()
        
        results = []
        for employee in employees:
            employee_data = {
                "id": str(employee.id),
                "employee_id": employee.employeeId,
                "en_full_name": employee.en_full_name,
                "vn_full_name": employee.vn_full_name,
                "email": employee.email,
            }
            
            point_data = FormulaService.calculate_ticket_point(
                employee_id=str(employee.id),
                month=month,
                formula_string=formula_string
            )
            
            results.append({
                "employee": employee_data,
                "task_count": point_data["task_count"],
                "bug_count": point_data["bug_count"],
                "point": point_data["ticket_point"],
                "breakdown": point_data["breakdown"]
            })
        
        results.sort(key=lambda x: x["point"], reverse=True)
        
        return results

