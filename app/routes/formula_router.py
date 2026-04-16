from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.services.formula_service import FormulaService
from app.responses import ApiResponse
from app.utils.decorators import admin_required
from app.dao.employee_dao import EmployeeDAO
from app.utils.query_helpers import parse_int_list_param, parse_list_param
from app.utils.round_float import _round_floats

formula_bp = Blueprint("formula", __name__)

@formula_bp.route("", methods=["GET"])
@jwt_required()
def get_formula():
    """Get all formulas and all parameters
    
    Query parameters:
    - month: Month number (1-12) - optional, defaults to current month
    
    Dynamic variables (computed at runtime):
    - TASK_COUNT: Number of completed tasks
    - BUG_COUNT: Number of completed bugs
    - LOG_HOURS: Total log hours for employee in month/year
    - TICKET_POINT: Ticket contribution point
    - LOGWORK_POINT: Logwork contribution point
    - MEMBER_CONTR_POINT: Member total contribution point (ticket + logwork)
    - TOTAL_TEAM_POINTS: Total team contribution points
    - BILLABLE_PARAM: Billable parameter from system
    
    Returns:
    {
        "success": true,
        "data": {
            "formulas": [
                {
                    "name": "TICKET_FORMULA_STRING",
                    "value": "(TASK_COUNT * TASK_WEIGHT + BUG_COUNT * BUG_WEIGHT) * ROLE_WEIGHT / STANDARD_ROLE"
                },
                {"name": "LOGWORK_FORMULA_STRING", "value": "LOG_HOURS / STANDARD_LOGWORK"},
                {"name": "MEMBER_CONTR_POINT_FORMULA_STRING", "value": "TICKET_POINT + LOGWORK_POINT"},
                {"name": "BILLABLE_POINT_FORMULA_STRING", "value": "MEMBER_CONTR_POINT / TOTAL_TEAM_POINTS * BILLABLE_PARAM"}
            ],
            "parameters": {
                "TASK_WEIGHT": "1",
                "BUG_WEIGHT": "2",
                "DEV_ROLE_WEIGHT": "1",
                "BA_ROLE_WEIGHT": "1",
                "QA_ROLE_WEIGHT": "1",
                "STANDARD_DEV": "100",
                "STANDARD_BA": "100",
                "STANDARD_QA": "100",
                "STANDARD_LOGWORK": "100",
                "BILLABLE_PARAM": "1000"
            },
            "dynamic_variables": {
                "TASK_COUNT": "Number of completed tasks",
                "BUG_COUNT": "Number of completed bugs",
                "LOG_HOURS": "Total log hours for employee in month/year",
                "TICKET_POINT": "Ticket contribution point",
                "LOGWORK_POINT": "Logwork contribution point",
                "MEMBER_CONTR_POINT": "Member total contribution point (ticket + logwork)",
                "TOTAL_TEAM_POINTS": "Total team contribution points",
                "BILLABLE_PARAM": "Billable parameter from system"
            }
        },
        "message": "Formulas retrieved successfully"
    }
    """
    # Get month parameter (optional, defaults to current month)
    month = request.args.get("month", type=int)
    
    # Validate month if provided
    if month is not None and (month < 1 or month > 12):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400
    
    data = FormulaService.get_formula(month)
    data = _round_floats(data)
    return ApiResponse.success(data=data, message="Formulas retrieved successfully")


@formula_bp.route("", methods=["PUT"])
@jwt_required()
@admin_required
def update_formula():
    """Update formula string
    
    Request body:
    {
        "formula_string": "(TICKET_COUNT * TASK_WEIGHT + BUG_COUNT * BUG_WEIGHT) * ROLE_WEIGHT / STANDARD_ROLE",
        "formula_name": "TICKET_FORMULA_STRING",  // optional, defaults to TICKET_FORMULA_STRING
        "month": 1  // optional, defaults to current month
    }
    
    Returns:
    {
        "success": true,
        "data": { ... },
        "message": "Formula updated successfully"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    formula_string = data.get("formula_string")
    formula_name = data.get("formula_name", "TICKET_FORMULA_STRING")
    month = data.get("month")
    
    # Validate month if provided
    if month is not None and (month < 1 or month > 12):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400
    
    if not formula_string:
        return jsonify({
            "success": False,
            "message": "formula_string is required",
            "errors": None
        }), 400
    
    result = FormulaService.update_formula(formula_string, formula_name, month)
    result = _round_floats(result)
    
    return ApiResponse.success(data=result, message="Formula updated successfully")


@formula_bp.route("/params", methods=["PUT"])
@jwt_required()
@admin_required
def update_params():
    """Update formula parameters
    
    Request body:
    {
        "TASK_WEIGHT": 1,
        "BUG_WEIGHT": 2,
        "DEV_ROLE_WEIGHT": 1,
        "BA_ROLE_WEIGHT": 1,
        "QA_ROLE_WEIGHT": 1,
        "STANDARD_DEV": 100,
        "STANDARD_BA": 100,
        "STANDARD_QA": 100,
        "STANDARD_LOGWORK": 100,
        "BILLABLE_PARAM": 1000,
        "month": 1  // optional, defaults to current month
    }
    
    Returns:
    {
        "success": true,
        "data": { ... },
        "message": "Parameters updated successfully"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    # Extract month from data
    month = data.pop("month", None)
    
    # Validate month if provided
    if month is not None and (month < 1 or month > 12):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400
    
    result = FormulaService.update_params(data, month)
    result = _round_floats(result)
    
    return ApiResponse.success(data=result, message="Parameters updated successfully")


@formula_bp.route("/params", methods=["POST"])
@jwt_required()
@admin_required
def add_param():
    """Add new formula parameters or formulas
    
    Request body (array format):
    {
        "params": [
            {
                "param_key": "NEW_PARAM_1",
                "param_value": "value1",
                "description": "Optional description",
                "type": "param"  // or "formula", defaults to "param"
            },
            {
                "param_key": "NEW_FORMULA_STRING",
                "param_value": "(TASK_COUNT * CUSTOM_WEIGHT) * ROLE_WEIGHT",
                "type": "formula",
                "description": "Optional description"
            }
        ],
        "month": 1  // optional, defaults to current month
    }
    
    Returns:
    {
        "success": true,
        "data": { ... },
        "message": "Parameters added successfully"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    params = data.get("params")
    month = data.get("month")
    
    # Validate month if provided
    if month is not None and (month < 1 or month > 12):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400
    
    if not params or not isinstance(params, list):
        return jsonify({
            "success": False,
            "message": "params is required and must be an array",
            "errors": None
        }), 400
    
    # Validate each param in the array
    for idx, param in enumerate(params):
        if not isinstance(param, dict):
            return jsonify({
                "success": False,
                "message": f"params[{idx}] must be an object",
                "errors": None
            }), 400
        
        param_key = param.get("param_key")
        param_value = param.get("param_value")
        param_type = param.get("type", "param")
        
        if not param_key or not param_value:
            return jsonify({
                "success": False,
                "message": f"params[{idx}]: param_key and param_value are required",
                "errors": None
            }), 400
        
        if param_type not in ("param", "formula"):
            return jsonify({
                "success": False,
                "message": f"params[{idx}]: type must be 'param' or 'formula'",
                "errors": None
            }), 400
    
    result = FormulaService.add_params(params, month)
    result = _round_floats(result)
    
    return ApiResponse.success(data=result, message="Parameters added successfully")


@formula_bp.route("/kpi/closed-tickets", methods=["GET"])
@jwt_required()
@admin_required
def get_closed_ticket_kpi():
    """Get closed-ticket KPI with optional project and ticket-type filter.

    Query parameters:
    - month: Month number(s) (1-12) - supports single or comma-separated (e.g. month=2,3,4).
             Defaults to current month when not provided.
    - year: Year (optional, defaults to current year).
    - project: Project UUID to filter by (optional).
    - ticket_type_id: Ticket type UUID(s) to filter by, supports comma-separated (optional).

    Response includes:
    - total_tickets, total_tickets_open, total_tickets_closed, total_tickets_inqa
    - status_overview: per-status counts for donut chart
    - series / details: closed tickets by role per month (bar + line charts)
    - project_overview: per-project per-role table data
    """
    months = parse_int_list_param(request.args.get("month"))
    year = request.args.get("year", type=int)
    project_id = request.args.get("project")
    ticket_type_ids = parse_list_param(request.args.get("ticket_type_id"))

    if not months:
        months = [datetime.now().month]

    if any(m < 1 or m > 12 for m in months):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400

    data = FormulaService.get_closed_ticket_kpi(months, year=year, project_id=project_id, ticket_type_ids=ticket_type_ids)
    return ApiResponse.success(
        data=_round_floats(data),
        message="Closed ticket KPI retrieved successfully"
    )


@formula_bp.route("/list-employees-ee", methods=["GET"])
@jwt_required()
def get_employees_total_ee():
    """Get all active employees with their total EE (sum of allocationPercent).

    Returns:
    {
        "success": true,
        "data": [
            {"enFullName": "Tony Nguyen", "totalEE": 60},
            ...
        ],
        "message": "Employees EE retrieved successfully"
    }
    """
    data = FormulaService.get_employees_total_ee()
    return ApiResponse.success(data=data, message="Employees EE retrieved successfully")


@formula_bp.route("/calculate", methods=["GET"])
@jwt_required()
@admin_required
def calculate_points_get():
    """Calculate all points for all employees (GET)
    
    Query parameters:
    - month: Month number(s) (1-12) - required, supports single or comma-separated (e.g. month=2,3,4)
    - year: Year (optional, defaults to current year)
    - employeeuuid: Filter by employee UUID (optional)
    - latest: If true, recalculate. If false (default), fetch from stored data.
    
    Returns:
    {
        "success": true,
        "data": {
            "results": [
                {
                    "employee": {
                        "id": "uuid",
                        "employeeId": "EMP001",
                        "en_full_name": "John Doe",
                        "vn_full_name": "Nguyen Van A",
                        "email": "john@company.com"
                    },
                    "month": 1,
                    "year": 2026,
                    "task_count": 5,
                    "bug_count": 3,
                    "ticket_point": 11.5,
                    "logwork_point": 8.0,
                    "member_contr_point": 19.5,
                    "total_team_points": 100.0,
                    "billable_point": 195.0,
                    "ticket_breakdown": [
                        {"role": "DEV", "value": 0.11},
                        {"role": "BA", "value": 0.11}
                    ]
                },
                ...
            ],
            "average_billable_point": 123.45,
            "total_billable_point": 987.65
        },
        "message": "Points calculated successfully"
    }
    """
    # Get query parameters - month supports single or comma-separated list (e.g. month=2,3,4)
    months = parse_int_list_param(request.args.get("month"))
    year = request.args.get("year", type=int)
    employeeuuid = request.args.get("employeeuuid")
    project_id = request.args.get("project")
    latest = request.args.get("latest", type=lambda x: x.lower() == "true", default=True)

    # Default month filter to current month when not provided
    if not months:
        months = [datetime.now().month]
    
    if any(m < 1 or m > 12 for m in months):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400
    
    # Calculate points for each month and combine results
    all_results = []
    monthly_average_billable_points = []
    monthly_total_billable_points = []
    monthly_average_ees = []
    total_ticket_point = 0.0
    total_logwork_point = 0.0
    total_tickets_closed = 0
    total_tickets_inqa = 0
    total_tickets = 0
    # params = []
    for month in months:
        results, average_billable_point, total_billable_point, monthly_ticket_point, monthly_logwork_point, average_ee = FormulaService.calculate_all_employees(
            month=month,
            year=year,
            employeeuuid=employeeuuid,
            latest=latest,
            project_id=project_id,
        )

        total_tickets_closed += FormulaService.count_tickets(
            month=month,
            employeeuuid=employeeuuid,
            status_id="CLOSED",
        )
        total_tickets_inqa += FormulaService.count_tickets(
            month=month,
            employeeuuid=employeeuuid,
            status_id="IN_QA",
        )
        total_tickets += FormulaService.count_tickets(
            month=month,
            employeeuuid=employeeuuid,
        )

        # param = FormulaService.get_formula(month)["parameters"]
        # params.append({
        #     "month": month,
        #     "param": param
        # })

        all_results.extend(results)
        monthly_average_billable_points.append(average_billable_point)
        monthly_total_billable_points.append(total_billable_point)
        monthly_average_ees.append(average_ee)
        total_ticket_point += monthly_ticket_point
        total_logwork_point += monthly_logwork_point

    average_billable_point = (
        sum(monthly_average_billable_points) / len(monthly_average_billable_points)
        if monthly_average_billable_points else 0.0
    )
    average_ee = (
        sum(monthly_average_ees) / len(monthly_average_ees)
        if monthly_average_ees else 0.0
    )

    total_billable_point = sum(monthly_total_billable_points) if monthly_total_billable_points else 0.0
    logwork_standard = FormulaService.get_logwork_standard_total(months)
    logwork_comparison = FormulaService.calculate_logwork_comparison(
        months=months,
        year=year,
        project_id=project_id,
        employeeuuid=employeeuuid,
    )
    ticket_comparison = FormulaService.calculate_ticket_comparison(
        months=months,
        year=year,
        project_id=project_id,
        employeeuuid=employeeuuid,
    )

    billable_standard = FormulaService.get_billable_standard_total(months)
    
    # If multiple months, aggregate results per employee (1 record per employee)
    if len(months) > 1:
        employee_map = {}
        for record in all_results:
            emp_id = record["employee_id"]
            if emp_id not in employee_map:
                employee_map[emp_id] = {
                    "employee_id": emp_id,
                    "employee": record.get("employee"),
                    "year": record.get("year"),
                    "months": [],
                    "task_count": 0,
                    "bug_count": 0,
                    "ticket_point": 0.0,
                    "logwork_point": 0.0,
                    "member_contr_point": 0.0,
                    "billable_point": 0.0,
                    "total_team_points": 0.0,
                    "ticket_breakdown": [],
                    "member_performance": {
                        "performance_level": "Bad",
                        "total_ee": 0.0,
                        "performance_result": 0.0,
                    },
                }
            entry = employee_map[emp_id]
            entry["months"].append(record.get("month"))
            entry["task_count"] += record.get("task_count", 0)
            entry["bug_count"] += record.get("bug_count", 0)
            entry["ticket_point"] += record.get("ticket_point", 0.0)
            entry["logwork_point"] += record.get("logwork_point", 0.0)
            entry["member_contr_point"] += record.get("member_contr_point", 0.0)
            entry["billable_point"] += record.get("billable_point", 0.0)
            entry["total_team_points"] += record.get("total_team_points", 0.0)
            entry["ticket_breakdown"].extend(record.get("ticket_breakdown", []))
            if record.get("member_performance"):
                perf = record.get("member_performance") or {}
                entry["member_performance"]["performance_result"] += perf.get("performance_result", 0.0)
                if perf.get("total_ee"):
                    entry["member_performance"]["total_ee"] = perf.get("total_ee")

        for entry in employee_map.values():
            unique_month_count = len(set(entry.get("months", []))) or len(months)
            perf = entry.get("member_performance") or {}
            total_ee = perf.get("total_ee", 0.0)
            performance_result = perf.get("performance_result", 0.0)
            entry["member_performance"] = FormulaService.build_member_performance(
                total_ee=total_ee,
                performance_result=performance_result,
                month_count=unique_month_count,
            )

        all_results = list(employee_map.values())

    _PERFORMANCE_ORDER = {"Excellent": 0, "Good": 1, "Bad": 2}
    all_results.sort(key=lambda x: (
        _PERFORMANCE_ORDER.get(
            (x.get("member_performance") or {}).get("performance_level", "Bad"), 99
        ),
        -x.get("ticket_point", 0)
    ))
    
    params = FormulaService.get_formula(month)["parameters"] #this return first month
    
    _data = _round_floats({
            "results": all_results,
            "params": params,
            "average_billable_point": average_billable_point,
            "total_billable_point": total_billable_point,
            "total_ticket_point": total_ticket_point,
            "total_logwork_point": total_logwork_point,
            "total_tickets_closed": total_tickets_closed,
            "total_tickets_inqa": total_tickets_inqa,
            "total_tickets": total_tickets,
            "billable_standard": billable_standard,
            "logwork_standard": logwork_standard,
            "logwork_comparison": logwork_comparison,
            "ticket_comparison": ticket_comparison,
            "average_ee": average_ee,
            "total_current_member": FormulaService.get_employee_count_with_tickets(months, project_id=project_id),
        })
    _data["total_billable_point"] = round(total_billable_point, 3)
    return ApiResponse.success(
        data=_data,
        message="Points calculated successfully"
    )

@formula_bp.route("/calculate/<string:employee_id>", methods=["GET"])
@jwt_required()
def calculate_employee_point(employee_id: str):
    """Calculate all points for a single employee
    
    Query parameters:
    - month: Month number(s) (1-12) - optional, supports single or comma-separated (e.g. month=1,2,3)
    - year: Year (optional, defaults to current year)
    - latest: If true, recalculate. If false (default), fetch from stored data.
    
    Returns:
    {
        "success": true,
        "data": {
            "employee_id": "uuid",
            "month": 1,
            "year": 2026,
            "task_count": 5,
            "bug_count": 3,
            "ticket_point": 11.5,
            "logwork_point": 8.0,
            "member_contr_point": 19.5,
            "total_team_points": 100.0,
            "billable_point": 195.0,
            "ticket_breakdown": [...]
        },
        "message": "Point calculated successfully"
    }
    """
    months = parse_int_list_param(request.args.get("month"))
    raw_month = months
    year = request.args.get("year", type=int)
    project_id = request.args.get("project")
    latest_raw = request.args.get("latest")
    if latest_raw is None or latest_raw == "":
        latest = True
    else:
        latest = latest_raw.lower() == "true"

    print(
        f"[calculate_employee_point] start employee_id={employee_id}, raw_month={request.args.get('month')}, parsed_months={months}, year={year}, latest_raw={latest_raw}, latest={latest}",
        flush=True,
    )

    # Default month filter to current month when not provided
    if not months:
        months = [datetime.now().month]

    if any(m < 1 or m > 12 for m in months):
        return jsonify({
            "success": False,
            "message": "month must be between 1 and 12",
            "errors": None
        }), 400
    
    # Verify employee exists
    employee = EmployeeDAO.get_by_id(employee_id)
    if not employee:
        return jsonify({
            "success": False,
            "message": "Employee not found",
            "errors": None
        }), 404
    
    # Get current year if not provided
    if not year:
        year = datetime.now().year

    # For single-employee endpoint, only keep months where employee has logwork
    print(
        f"[calculate_employee_point] before_logwork_filter employee_id={employee.id}, months={months}, year={year}",
        flush=True,
    )
    months = FormulaService.filter_months_with_logwork(str(employee.id), months, year)
    print(
        f"[calculate_employee_point] after_logwork_filter employee_id={employee.id}, months={months}",
        flush=True,
    )

    logwork_standard = FormulaService.get_logwork_standard_total(months)
    billable_standard = FormulaService.get_billable_standard_total(months)

    if not months:
        print(
            f"[calculate_employee_point] no_logwork_data employee_id={employee.id}, year={year}, requested_months={request.args.get('month')}",
            flush=True,
        )
        params = FormulaService.get_formula(raw_month)["parameters"]
        return ApiResponse.success(
            data=_round_floats({
                "results": [],
                "average_billable_point": 0.0,
                "total_billable_point": 0.0,
                "total_ticket_point": 0.0,
                "total_logwork_point": 0.0,
                "billable_standard": billable_standard,
                "logwork_standard": logwork_standard,
                "params": params,
                "average_ee": 0.0,
            }),
            message="No logwork data found for selected month(s)"
        )
    
    print(f"[calculate_employee_point] months_for_calculation={months}", flush=True)
    # Calculate all points for the employee
    # result = FormulaService.calculate_employee_all_points(
    #     employee_id=employee_id,
    #     month=month,
    #     year=year,
    #     latest=latest
    # )

    all_results = []
    monthly_average_billable_points = []
    monthly_average_ees = []
    total_billable_point = 0.0
    total_ticket_point = 0.0
    total_logwork_point = 0.0

    for month in months:
        result, average_billable_point, monthly_total_billable_point, monthly_total_ticket_point, monthly_total_logwork_point, average_ee = FormulaService.calculate_all_employees(
            month=month,
            year=year,
            employeeuuid=str(employee.id),
            latest=latest,
            project_id=project_id,
        )
        all_results.extend(result)
        monthly_average_billable_points.append(average_billable_point)
        monthly_average_ees.append(average_ee)
        total_billable_point += monthly_total_billable_point
        total_ticket_point += monthly_total_ticket_point
        total_logwork_point += monthly_total_logwork_point

    average_billable_point = (
        sum(monthly_average_billable_points) / len(monthly_average_billable_points)
        if monthly_average_billable_points else 0.0
    )
    average_ee = (
        sum(monthly_average_ees) / len(monthly_average_ees)
        if monthly_average_ees else 0.0
    )

    # If multiple months are selected, aggregate into one combined employee record
    if len(months) > 1 and all_results:
        combined = {
            "employee_id": all_results[0].get("employee_id"),
            "employee": all_results[0].get("employee"),
            "year": all_results[0].get("year"),
            "months": sorted({r.get("month") for r in all_results if r.get("month") is not None}),
            "task_count": 0,
            "bug_count": 0,
            "ticket_point": 0.0,
            "logwork_point": 0.0,
            "member_contr_point": 0.0,
            "billable_point": 0.0,
            "total_team_points": 0.0,
            "ticket_breakdown": [],
            "member_performance": {
                "performance_level": "Bad",
                "total_ee": 0.0,
                "performance_result": 0.0,
            },
        }

        for record in all_results:
            combined["task_count"] += record.get("task_count", 0)
            combined["bug_count"] += record.get("bug_count", 0)
            combined["ticket_point"] += record.get("ticket_point", 0.0)
            combined["logwork_point"] += record.get("logwork_point", 0.0)
            combined["member_contr_point"] += record.get("member_contr_point", 0.0)
            combined["billable_point"] += record.get("billable_point", 0.0)
            combined["total_team_points"] += record.get("total_team_points", 0.0)
            combined["ticket_breakdown"].extend(record.get("ticket_breakdown", []))
            if record.get("member_performance"):
                perf = record.get("member_performance") or {}
                combined["member_performance"]["performance_result"] += perf.get("performance_result", 0.0)
                if perf.get("total_ee"):
                    combined["member_performance"]["total_ee"] = perf.get("total_ee")

        unique_month_count = len(set(combined.get("months", []))) or len(months)
        perf = combined.get("member_performance") or {}
        combined["member_performance"] = FormulaService.build_member_performance(
            total_ee=perf.get("total_ee", 0.0),
            performance_result=perf.get("performance_result", 0.0),
            month_count=unique_month_count,
        )

        all_results = [combined]
    else:
        all_results.sort(key=lambda x: x.get("month", 0))

    print(f"Calculated points for employee {employee_id} in months {months}/{year}: {all_results}")
    
    # Also calculate total team points and billable for single employee
    # Need to get all employees to calculate total team points
    # all_results = FormulaService.calculate_all_employees(
    #     month=month,
    #     year=year,
    #     employeeuuid=employee_id,
    #     latest=latest
    # )
    
    # if all_results:
    #     result["total_team_points"] = all_results[0].get("total_team_points", 0)
    #     result["billable_point"] = all_results[0].get("billable_point", 0)
    
    params = FormulaService.get_formula(month)["parameters"]
    
    _data = _round_floats({
            "results": all_results,
            "average_billable_point": average_billable_point,
            "total_billable_point": total_billable_point,
            "total_ticket_point": total_ticket_point,
            "total_logwork_point": total_logwork_point,
            "billable_standard": billable_standard,
            "logwork_standard": logwork_standard,
            "params": params,
            "average_ee": average_ee
        })
    _data["total_billable_point"] = round(total_billable_point, 3)
    return ApiResponse.success(
        data=_data,
        message="Point calculated successfully"
    )

