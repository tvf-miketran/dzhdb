from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import calendar

from app.requests.ticket_request import CreateTicketRequest, UpdateTicketRequest
from app.services.ticket_service import TicketService
from app.responses import ApiResponse
from app.utils.decorators import admin_required
from app.utils.query_helpers import parse_list_param, parse_int_list_param
from app.dao.employee_dao import EmployeeDAO

ticket_bp = Blueprint("ticket", __name__)


def calculate_weeks_in_month(month: int, year: int = None) -> list:
    """Calculate weeks in a month
    
    Args:
        month: Month number (1-12)
        year: Year (default: current year)
    
    Returns:
        List of week strings like "1 (01/01/2026-04/01/2026)"
    """
    if year is None:
        year = datetime.now().year
    
    # Get the first day of the month
    first_day = datetime(year, month, 1)
    
    # Get the last day of the month
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    weeks = []
    week_num = 1
    
    # Week 1: from day 1 to the first Sunday
    # weekday(): Monday=0, ..., Saturday=5, Sunday=6
    first_sunday = first_day + timedelta(days=(6 - first_day.weekday()))
    
    # Don't go past last day of month
    if first_sunday > last_day:
        first_sunday = last_day
    
    week_str = f"{week_num} ({first_day.strftime('%d/%m/%Y')}-{first_sunday.strftime('%d/%m/%Y')})"
    weeks.append(week_str)
    
    # Subsequent weeks: start from next Monday
    week_start = first_sunday + timedelta(days=1)
    week_num = 2
    
    while week_start <= last_day:
        # Week ends on Sunday
        week_end = week_start + timedelta(days=6)
        
        # Don't go past last day of month
        if week_end > last_day:
            week_end = last_day
        
        # Format the week string
        week_str = f"{week_num} ({week_start.strftime('%d/%m/%Y')}-{week_end.strftime('%d/%m/%Y')})"
        weeks.append(week_str)
        
        # Move to next Monday
        week_start = week_end + timedelta(days=1)
        week_num += 1
    
    return weeks


@ticket_bp.route("/weeks", methods=["POST"])
def get_weeks_in_month():
    """Calculate weeks in a month
    
    Request body:
    {
        "month": "1"  // Month number (1-12), required
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "weeks": ["1 (01/02/2026-07/02/2026)", "2 (08/02/2026-15/02/2026)"]
        },
        "message": "Weeks calculated successfully"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    month = data.get("month")
    
    if not month:
        return jsonify({
            "success": False,
            "message": "Month is required",
            "errors": None
        }), 400
    
    # Parse month
    try:
        month = int(month)
        if month < 1 or month > 12:
            return jsonify({
                "success": False,
                "message": "Month must be between 1 and 12",
                "errors": None
            }), 400
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid month format",
            "errors": None
        }), 400
    
    # Calculate weeks
    weeks = calculate_weeks_in_month(month)
    
    return ApiResponse.success(
        data={"weeks": weeks},
        message="Weeks calculated successfully"
    )


@ticket_bp.route("", methods=["GET"])
@jwt_required()
@admin_required
def get_all_tickets():
    """Get all tickets with pagination, filtering, and sorting (Admin only)
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - project_id: Filter by project UUID(s) - can be single UUID or comma-separated "uuid1,uuid2,uuid3"
    - employee_id: Filter by employee UUID(s) - can be single UUID or comma-separated
    - ticket_type_id: Filter by ticket type UUID(s) - can be single UUID or comma-separated
    - ticket_status_id: Filter by ticket status UUID(s) - can be single UUID or comma-separated
    - week: Filter by week number(s) - can be single or comma-separated
    - month: Filter by month number(s) - can be single or comma-separated
    - search: Search by ticket_id or ticket_link
    - sort_by: Sort field (created_at, updated_at, ticket_id)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    # Get pagination params
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Get filter params - all support single or comma-separated multiple values
    project_id = parse_list_param(request.args.get("project_id"))
    employee_id = parse_list_param(request.args.get("employee_id"))
    ticket_type_id = parse_list_param(request.args.get("ticket_type_id"))
    ticket_status_id = parse_list_param(request.args.get("ticket_status_id"))
    week = parse_int_list_param(request.args.get("week"))
    month = parse_int_list_param(request.args.get("month"))
    search = request.args.get("search", type=str)
    
    # Get sort params
    sort_by = request.args.get("sort_by", "created_at", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)
    
    # If no pagination, apply filters and return results
    if not page:
        tickets = TicketService.get_all()
        
        # Apply filters
        filtered_tickets = tickets
        if project_id:
            if len(project_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.project_id) == project_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.project_id) in project_id]
        if employee_id:
            if len(employee_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.employee_id) == employee_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.employee_id) in employee_id]
        if ticket_type_id:
            if len(ticket_type_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_type_id) == ticket_type_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_type_id) in ticket_type_id]
        if ticket_status_id:
            if len(ticket_status_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_status_id) == ticket_status_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_status_id) in ticket_status_id]
        if week:
            if len(week) == 1:
                filtered_tickets = [t for t in filtered_tickets if t.week == week[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if t.week in week]
        if month:
            if len(month) == 1:
                filtered_tickets = [t for t in filtered_tickets if t.month == month[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if t.month in month]
        if search:
            search_lower = search.lower()
            filtered_tickets = [
                t for t in filtered_tickets 
                if search_lower in t.ticket_id.lower() or 
                (t.ticket_link and search_lower in t.ticket_link.lower())
            ]
        
        data = [TicketService._to_dict(ticket) for ticket in filtered_tickets]
        return ApiResponse.success(
            data=data, 
            message=f"Tickets retrieved successfully (total: {len(data)})"
        )
    
    # Get filtered and sorted paginated results
    result = TicketService.get_all_filtered_sorted(
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
    
    return ApiResponse.success(data=result, message="Tickets retrieved successfully")


@ticket_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_tickets():
    """Get all tickets assigned to current user with pagination, filtering, and sorting
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - project_id: Filter by project UUID(s) - can be single UUID or comma-separated "uuid1,uuid2,uuid3"
    - ticket_type_id: Filter by ticket type UUID(s) - can be single UUID or comma-separated
    - ticket_status_id: Filter by ticket status UUID(s) - can be single UUID or comma-separated
    - week: Filter by week number(s) - can be single or comma-separated
    - month: Filter by month number(s) - can be single or comma-separated
    - search: Search by ticket_id or ticket_link
    - sort_by: Sort field (created_at, updated_at, ticket_id)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    # Get current user employeeID from JWT (this is the employeeId string like "EMP001")
    employee_id_str = get_jwt_identity()
    
    if not employee_id_str:
        return jsonify({
            "success": False,
            "message": "User not found",
            "errors": None
        }), 404
    
    # Get employee UUID from employeeID string
    employee = EmployeeDAO.get_by_employee_id(employee_id_str)
    if not employee:
        return jsonify({
            "success": False,
            "message": "Employee not found",
            "errors": None
        }), 404
    
    # Get the UUID of the employee
    current_user_uuid = str(employee.id)
    
    # Get pagination params
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Get filter params - all support single or comma-separated multiple values
    # Note: No employee_id filter since it's automatically filtered by current user
    project_id = parse_list_param(request.args.get("project_id"))
    ticket_type_id = parse_list_param(request.args.get("ticket_type_id"))
    ticket_status_id = parse_list_param(request.args.get("ticket_status_id"))
    week = parse_int_list_param(request.args.get("week"))
    month = parse_int_list_param(request.args.get("month"))
    search = request.args.get("search", type=str)
    
    # Get sort params
    sort_by = request.args.get("sort_by", "created_at", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)
    
    # If no pagination, apply filters and return results
    if not page:
        tickets = TicketService.get_all()
        
        # Filter by current user first
        filtered_tickets = [t for t in tickets if str(t.employee_id) == current_user_uuid]
        
        # Apply filters
        if project_id:
            if len(project_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.project_id) == project_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.project_id) in project_id]
        if ticket_type_id:
            if len(ticket_type_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_type_id) == ticket_type_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_type_id) in ticket_type_id]
        if ticket_status_id:
            if len(ticket_status_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_status_id) == ticket_status_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_status_id) in ticket_status_id]
        if week:
            if len(week) == 1:
                filtered_tickets = [t for t in filtered_tickets if t.week == week[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if t.week in week]
        if month:
            if len(month) == 1:
                filtered_tickets = [t for t in filtered_tickets if t.month == month[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if t.month in month]
        if search:
            search_lower = search.lower()
            filtered_tickets = [
                t for t in filtered_tickets 
                if search_lower in t.ticket_id.lower() or 
                (t.ticket_link and search_lower in t.ticket_link.lower())
            ]
        
        data = [TicketService._to_dict(ticket) for ticket in filtered_tickets]
        return ApiResponse.success(
            data=data, 
            message=f"My tickets retrieved successfully (total: {len(data)})"
        )
    
    # Get filtered and sorted paginated results (with current user filter)
    result = TicketService.get_all_filtered_sorted(
        page=page,
        per_page=per_page,
        project_id=project_id,
        employee_id=[current_user_uuid],  # Force filter by current user
        ticket_type_id=ticket_type_id,
        ticket_status_id=ticket_status_id,
        week=week,
        month=month,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return ApiResponse.success(data=result, message="My tickets retrieved successfully")


@ticket_bp.route("/<string:id>", methods=["GET"])
@jwt_required()
def get_ticket(id: str):
    """Get ticket by ID (UUID or ticket_id)"""
    # Try to get by UUID first
    ticket = TicketService.get_by_id(id)
    
    # If not found by UUID, try by ticket_id
    if not ticket:
        ticket = TicketService.get_by_ticket_id(id)
    
    if not ticket:
        return jsonify({
            "success": False,
            "message": "Ticket not found",
            "errors": None
        }), 404
    
    data = TicketService._to_dict(ticket)
    
    return ApiResponse.success(data=data, message="Ticket retrieved successfully")


@ticket_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_ticket():
    """Create new ticket (Admin only)
    
    Request body:
    {
        "ticketId": "TICKET001",
        "projectId": "uuid-string" (required),
        "ticketLink": "https://..." (optional),
        "roleIds": ["uuid-string"] (optional, array of role UUIDs),
        "employeeId": "uuid-string" (optional, assignee),
        "ticketTypeId": "uuid-string" (optional),
        "ticketStatusId": "uuid-string" (optional),
        "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
        "month": 1 (optional)
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    # Validate request
    req, errors = CreateTicketRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Create ticket
    ticket, create_errors, message = TicketService.create(
        ticket_id=req.ticket_id,
        project_id=req.project_id,
        ticket_link=req.ticket_link,
        role_ids=req.role_ids,
        employee_id=req.employee_id,
        ticket_type_id=req.ticket_type_id,
        ticket_status_id=req.ticket_status_id,
        week=req.week,
        month=req.month
    )
    
    if create_errors:
        return jsonify({
            "success": False,
            "message": "Failed to create ticket",
            "errors": create_errors
        }), 400
    
    response_data = TicketService._to_dict(ticket)
    
    # Use the returned message if available (e.g., when ticket already exists and was updated)
    success_message = message if message else "Ticket created successfully"
    
    return ApiResponse.success(
        data=response_data,
        message=success_message,
        status_code=201
    )


@ticket_bp.route("/bulk", methods=["POST"])
@jwt_required()
@admin_required
def create_tickets():
    """Create multiple tickets (Admin only)
    
    Request body:
    {
        "tickets": [
            {
                "ticketId": "TICKET001",
                "projectId": "uuid-string" (required),
                "ticketLink": "https://..." (optional),
                "roleIds": ["uuid-string"] (optional, array of role UUIDs),
                "employeeId": "uuid-string" (optional, assignee),
                "ticketTypeId": "uuid-string" (optional),
                "ticketStatusId": "uuid-string" (optional),
                "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
                "month": 1 (optional)
            },
            ...
        ]
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    tickets_data = data.get("tickets")
    
    if not tickets_data or not isinstance(tickets_data, list):
        return jsonify({
            "success": False,
            "message": "Tickets array is required",
            "errors": None
        }), 400
    
    created_tickets = []
    errors_list = []
    
    for idx, ticket_data in enumerate(tickets_data):
        # Validate each ticket
        req, errors = CreateTicketRequest.from_dict(ticket_data)
        
        if errors:
            errors_list.append({
                "index": idx,
                "ticketId": ticket_data.get("ticketId", "unknown"),
                "errors": errors
            })
            continue
        
        # Create ticket
        ticket, create_errors, message = TicketService.create(
            ticket_id=req.ticket_id,
            project_id=req.project_id,
            ticket_link=req.ticket_link,
            role_ids=req.role_ids,
            employee_id=req.employee_id,
            ticket_type_id=req.ticket_type_id,
            ticket_status_id=req.ticket_status_id,
            week=req.week,
            month=req.month
        )
        
        if create_errors:
            errors_list.append({
                "index": idx,
                "ticketId": req.ticket_id,
                "errors": create_errors
            })
        else:
            created_tickets.append(TicketService._to_dict(ticket))
    
    if not created_tickets:
        return jsonify({
            "success": False,
            "message": "Failed to create any tickets",
            "errors": errors_list
        }), 400
    
    return ApiResponse.success(
        data={
            "created": created_tickets,
            "total_created": len(created_tickets),
            "errors": errors_list
        },
        message=f"Successfully created {len(created_tickets)} tickets",
        status_code=201
    )


@ticket_bp.route("/<string:id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_ticket(id: str):
    """Update ticket (Admin only)
    
    Request body:
    {
        "ticketId": "TICKET002" (optional),
        "ticketLink": "https://..." (optional),
        "projectId": "uuid-string" (optional),
        "roleIds": ["uuid-string"] (optional, array of role UUIDs),
        "employeeId": "uuid-string" (optional),
        "ticketTypeId": "uuid-string" (optional),
        "ticketStatusId": "uuid-string" (optional),
        "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
        "month": 1 (optional)
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    # Validate request
    req, errors = UpdateTicketRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Update ticket
    ticket, update_errors = TicketService.update(
        id=id,
        ticket_id=req.ticket_id,
        ticket_link=req.ticket_link,
        project_id=req.project_id,
        role_ids=req.role_ids,
        employee_id=req.employee_id,
        ticket_type_id=req.ticket_type_id,
        ticket_status_id=req.ticket_status_id,
        week=req.week,
        month=req.month
    )
    
    if update_errors:
        status_code = 404 if "not found" in update_errors[0].lower() else 400
        return jsonify({
            "success": False,
            "message": update_errors[0],
            "errors": update_errors
        }), status_code
    
    response_data = TicketService._to_dict(ticket)
    
    return ApiResponse.success(data=response_data, message="Ticket updated successfully")


@ticket_bp.route("/<string:id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_ticket(id: str):
    """Delete ticket (Admin only)"""
    success, errors = TicketService.delete(id)
    
    if not success:
        return jsonify({
            "success": False,
            "message": "Failed to delete ticket",
            "errors": errors
        }), 404
    
    return ApiResponse.success(data=None, message="Ticket deleted successfully")


@ticket_bp.route("/project/<string:project_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_tickets_by_project(project_id: str):
    """Get all tickets for a specific project (Admin only)
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - ticket_type_id: Filter by ticket type UUID(s) - can be single UUID or comma-separated
    - ticket_status_id: Filter by ticket status UUID(s) - can be single UUID or comma-separated
    - employee_id: Filter by employee UUID(s) - can be single UUID or comma-separated
    - week: Filter by week number(s) - can be single or comma-separated
    - month: Filter by month number(s) - can be single or comma-separated
    - search: Search by ticket_id or ticket_link
    - sort_by: Sort field (created_at, updated_at, ticket_id)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    # Get pagination params
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Get filter params - all support single or comma-separated multiple values
    ticket_type_id = parse_list_param(request.args.get("ticket_type_id"))
    ticket_status_id = parse_list_param(request.args.get("ticket_status_id"))
    employee_id = parse_list_param(request.args.get("employee_id"))
    week = parse_int_list_param(request.args.get("week"))
    month = parse_int_list_param(request.args.get("month"))
    search = request.args.get("search", type=str)
    
    # Get sort params
    sort_by = request.args.get("sort_by", "created_at", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)
    
    # If no pagination, return all tickets for project
    if not page:
        tickets = TicketService.get_by_project_id(project_id)
        
        # Apply filters manually for non-paginated request
        filtered_tickets = tickets
        if ticket_type_id:
            if len(ticket_type_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_type_id) == ticket_type_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_type_id) in ticket_type_id]
        if ticket_status_id:
            if len(ticket_status_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_status_id) == ticket_status_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.ticket_status_id) in ticket_status_id]
        if employee_id:
            if len(employee_id) == 1:
                filtered_tickets = [t for t in filtered_tickets if str(t.employee_id) == employee_id[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if str(t.employee_id) in employee_id]
        if week:
            if len(week) == 1:
                filtered_tickets = [t for t in filtered_tickets if t.week == week[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if t.week in week]
        if month:
            if len(month) == 1:
                filtered_tickets = [t for t in filtered_tickets if t.month == month[0]]
            else:
                filtered_tickets = [t for t in filtered_tickets if t.month in month]
        if search:
            search_lower = search.lower()
            filtered_tickets = [
                t for t in filtered_tickets 
                if search_lower in t.ticket_id.lower() or 
                (t.ticket_link and search_lower in t.ticket_link.lower())
            ]
        
        data = [TicketService._to_dict(ticket) for ticket in filtered_tickets]
        return ApiResponse.success(
            data=data, 
            message=f"Tickets for project retrieved successfully (total: {len(data)})"
        )
    
    # Get filtered and sorted paginated results
    result = TicketService.get_all_filtered_sorted(
        page=page,
        per_page=per_page,
        project_id=[project_id],  # Pass as list since this endpoint is for specific project
        employee_id=employee_id,
        ticket_type_id=ticket_type_id,
        ticket_status_id=ticket_status_id,
        week=week,
        month=month,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return ApiResponse.success(data=result, message="Tickets for project retrieved successfully")

