from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import calendar

from app.requests.ticket_request import CreateTicketRequest, UpdateTicketRequest
from app.services.ticket_service import TicketService
from app.responses import ApiResponse
from app.utils.decorators import admin_required
from app.utils.auth_helpers import get_current_user
from app.utils.query_helpers import parse_list_param, parse_int_list_param
from app.dao.employee_dao import EmployeeDAO
from sqlalchemy.exc import DataError

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
        tickets = TicketService.get_all_filtered(
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

        data = [TicketService._to_dict(ticket) for ticket in tickets]
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
        tickets = TicketService.get_my_filtered(
            project_id=project_id,
            employee_id=[current_user_uuid],
            ticket_type_id=ticket_type_id,
            ticket_status_id=ticket_status_id,
            week=week,
            month=month,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        data = [TicketService._to_dict(ticket) for ticket in tickets]
        return ApiResponse.success(
            data=data, 
            message=f"My tickets retrieved successfully (total: {len(data)})"
        )
    
    # Get filtered and sorted paginated results (with current user filter)
    result = TicketService.get_my_filtered_sorted(
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
    """Get ticket by ID (UUID or ticket_id pattern with LIKE search)"""
    # Try to get by UUID first
    # Catch both ValueError (invalid UUID format) and DataError (SQLAlchemy UUID type error)
    try:
        ticket = TicketService.get_by_id(id)
    except (ValueError, DataError):
        ticket = None
    
    # If not found by UUID, try by ticket_id exact match
    if not ticket:
        ticket = TicketService.get_by_ticket_id(id)
    
    # If still not found, try LIKE search (e.g., "ABC-123" will match "ABC-123", "ABC-123(1)", etc.)
    if not ticket:
        tickets = TicketService.get_by_ticket_id_like(id)
        
        if tickets:
            # Return all matching tickets
            data = [TicketService._to_dict(t) for t in tickets]
            return ApiResponse.success(
                data=data, 
                message=f"Found {len(data)} ticket(s) matching '{id}'"
            )
    
    if not ticket:
        return jsonify({
            "success": False,
            "message": "Ticket not found",
            "errors": None
        }), 404
    
    data = TicketService._to_dict(ticket)
    
    return ApiResponse.success(data=data, message="Ticket retrieved successfully")


@ticket_bp.route("/search", methods=["GET"])
@jwt_required()
def search_ticket_by_ticket_id():
    """Search ticket by ticket_id using LIKE pattern matching
    
    Query parameters:
    - query: The ticket ID or pattern to search (e.g., "AMI-4334")
    
    Returns:
    - Single ticket if exact match found
    - Multiple tickets if LIKE pattern matches
    - 400 if query is missing
    - 404 if no match found
    """
    # Get query parameter
    query = request.args.get("query", type=str)
    
    if not query or not query.strip():
        return jsonify({
            "success": False,
            "message": "Query parameter 'query' is required",
            "errors": None
        }), 400
    
    # Sanitize: limit length and trim whitespace
    query = query.strip()[:50]  # Limit to 50 characters
    
    # LIKE search - finds tickets matching pattern
    tickets = TicketService.get_by_ticket_id_like(query)
    
    if not tickets:
        return jsonify({
            "success": False,
            "message": f"No tickets found matching '{query}'",
            "errors": None
        }), 404
    
    # If only one result and it matches exactly, return single ticket
    if len(tickets) == 1 and tickets[0].ticket_id == query:
        data = TicketService._to_dict(tickets[0])
        return ApiResponse.success(data=data, message="Ticket found")
    
    # Multiple matches - return all
    data = [TicketService._to_dict(t) for t in tickets]
    return ApiResponse.success(
        data=data, 
        message=f"Found {len(data)} ticket(s) matching '{query}'"
    )


@ticket_bp.route("", methods=["POST"])
@jwt_required()
# @admin_required
def create_ticket():
    """Create new ticket (Admin only)
    
    Request body:
    {
        "ticketId": "TICKET001",
        "projectId": "uuid-string" (required),
        "ticketLink": "https://..." (optional),
        "roleIds": ["BA", "DEV", "EQA", "IQA", "REVIEWER"] (optional, array of role IDs),
        "employeeId": "uuid-string" (optional, assignee),
        "ticketTypeId": "uuid-string" (optional),
        "ticketStatusId": "uuid-string" (optional),
        "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
        "month": 1 (optional)
    }
    
    Note: roleIds now accepts roleID strings (BA, DEV, EQA, IQA, REVIEWER) instead of UUIDs.
          These will be resolved to UUIDs internally.
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
            "message": message if message else "Failed to create ticket",
            "errors": create_errors
        }), 400
    
    response_data = TicketService._to_dict(ticket)
    
    # Use the returned message if available (e.g., when ticket already exists)
    success_message = message if message else "Ticket created successfully"
    
    return ApiResponse.success(
        data=response_data,
        message=success_message,
        status_code=201
    )


@ticket_bp.route("/bulk", methods=["POST"])
@jwt_required()
# @admin_required
def create_tickets():
    """Create multiple tickets (Admin only)
    
    Request body:
    {
        "tickets": [
            {
                "ticketId": "TICKET001",
                "projectId": "uuid-string" (required),
                "ticketLink": "https://..." (optional),
                "roleIds": ["BA", "DEV", "EQA", "IQA", "REVIEWER"] (optional, array of role IDs),
                "employeeId": "uuid-string" (optional, assignee),
                "ticketTypeId": "uuid-string" (optional),
                "ticketStatusId": "uuid-string" (optional),
                "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
                "month": 1 (optional)
            },
            ...
        ]
    }
    
    Note: roleIds now accepts roleID strings (BA, DEV, EQA, IQA, REVIEWER) instead of UUIDs.
          These will be resolved to UUIDs internally.
    
    Response when mixed existing/new tickets:
    {
        "success": true,
        "data": {
            "created": [...],
            "existing": [...],
            "total_created": 2,
            "total_existing": 2,
            "errors": [...]
        },
        "message": "New tickets created with IDs CBA, DBA. Ticket IDs ABC, ABD already exist"
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
    
    # Prepare tickets data for bulk create
    tickets_to_create = []
    for ticket_data in tickets_data:
        # Validate each ticket
        req, errors = CreateTicketRequest.from_dict(ticket_data)
        
        if errors:
            continue
        
        tickets_to_create.append({
            "ticket_id": req.ticket_id,
            "project_id": req.project_id,
            "ticket_link": req.ticket_link,
            "role_ids": req.role_ids,
            "employee_id": req.employee_id,
            "ticket_type_id": req.ticket_type_id,
            "ticket_status_id": req.ticket_status_id,
            "week": req.week,
            "month": req.month
        })
    
    # Use bulk create method
    created_tickets, existing_tickets, errors = TicketService.create_bulk(tickets_to_create)
    
    # Build response data
    response_data = {
        "created": [TicketService._to_dict(t) for t in created_tickets],
        "total_created": len(created_tickets),
    }
    
    # Add existing tickets info
    if existing_tickets:
        response_data["existing"] = existing_tickets
        response_data["total_existing"] = len(existing_tickets)
    
    if errors:
        response_data["errors"] = errors
    
    # Build message based on results
    message_parts = []
    if created_tickets:
        created_ids = [t.ticket_id for t in created_tickets]
        message_parts.append(f"New tickets created with IDs {', '.join(created_ids)}")
    if existing_tickets:
        existing_ids = [e["ticketId"] for e in existing_tickets]
        message_parts.append(f"Ticket IDs {', '.join(existing_ids)} already exist")
    
    # If all tickets already exist, return success with existing tickets data
    if not created_tickets and existing_tickets:
        return ApiResponse.success(
            data=response_data,
            message=". ".join(message_parts),
            status_code=200
        )
    
    if not created_tickets and not existing_tickets:
        return jsonify({
            "success": False,
            "message": "Failed to create any tickets",
            "errors": errors
        }), 400
    
    message = ". ".join(message_parts) if message_parts else f"Successfully created {len(created_tickets)} tickets"
    
    return ApiResponse.success(
        data=response_data,
        message=message,
        status_code=201
    )


@ticket_bp.route("/<string:id>", methods=["PUT"])
@jwt_required()
# @admin_required
def update_ticket(id: str):
    """Update ticket
    
    Request body:
    {
        "ticketId": "TICKET002" (optional),
        "ticketLink": "https://..." (optional),
        "projectId": "uuid-string" (optional),
        "roleIds": ["BA", "DEV", "EQA", "IQA", "REVIEWER"] (optional, array of role IDs),
        "employeeId": "uuid-string" (optional),
        "ticketTypeId": "uuid-string" (optional),
        "ticketStatusId": "uuid-string" (optional),
        "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
        "month": 1 (optional)
    }
    
    Note: roleIds now accepts roleID strings (BA, DEV, EQA, IQA, REVIEWER) instead of UUIDs.
          These will be resolved to UUIDs internally.
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

    current_user = get_current_user()
    if not current_user:
        return jsonify({
            "success": False,
            "message": "User not found",
            "errors": None
        }), 404
    
    # Update ticket
    ticket, update_errors = TicketService.update(
        id=id,
        current_user_id=str(current_user.id),
        current_user_role=current_user.authorize_role,
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
        status_code = 400
        if any("not authorized" in err.lower() for err in update_errors):
            status_code = 403
        elif any("not found" in err.lower() for err in update_errors):
            status_code = 404

        return jsonify({
            "success": False,
            "message": update_errors[0],
            "errors": update_errors
        }), status_code
    
    response_data = TicketService._to_dict(ticket)
    
    return ApiResponse.success(data=response_data, message="Ticket updated successfully")


@ticket_bp.route("/bulk", methods=["PUT"])
@jwt_required()
# @admin_required
def update_tickets():
    """Update multiple tickets
    
    Request body:
    {
        "tickets": [
            {
                "id": "uuid-string" (required - UUID to identify ticket to update),
                "ticketId": "TICKET002" (optional - new ticket ID),
                "ticketLink": "https://..." (optional),
                "projectId": "uuid-string" (optional),
                "roleIds": ["BA", "DEV", "EQA", "IQA", "REVIEWER"] (optional, array of role IDs),
                "employeeId": "uuid-string" (optional),
                "ticketTypeId": "uuid-string" (optional),
                "ticketStatusId": "uuid-string" (optional),
                "week": "1 (01/01/2026-04/01/2026)" (optional) or just "1",
                "month": 1 (optional)
            },
            ...
        ]
    }
    
    Note: 
    - roleIds accepts roleID strings (BA, DEV, EQA, IQA, REVEWER) instead of UUIDs.
    - Each ticket must be identified by 'id' (UUID) - ticketId is for updating the ticket ID value.
    - Tickets not found will be returned in 'not_found' array with "Ticket not found" message.
    
    Response:
    {
        "success": true,
        "data": {
            "updated": [...],
            "not_found": [...],
            "errors": [...],
            "total_updated": 2,
            "total_not_found": 1,
            "total_errors": 0
        },
        "message": "2 ticket(s) updated successfully, 1 not found"
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

    current_user = get_current_user()
    if not current_user:
        return jsonify({
            "success": False,
            "message": "User not found",
            "errors": None
        }), 404
    
    # Use bulk update method
    updated_tickets, not_found_tickets, errors = TicketService.update_bulk(
        tickets_data=tickets_data,
        current_user_id=str(current_user.id),
        current_user_role=current_user.authorize_role
    )
    
    # Build response data
    response_data = {
        "updated": updated_tickets,
        "total_updated": len(updated_tickets),
    }
    
    # Add not found tickets info
    if not_found_tickets:
        response_data["not_found"] = not_found_tickets
        response_data["total_not_found"] = len(not_found_tickets)
    
    if errors:
        response_data["errors"] = errors
        response_data["total_errors"] = len(errors)
    
    # Build message based on results
    message_parts = []
    if updated_tickets:
        message_parts.append(f"{len(updated_tickets)} ticket(s) updated successfully")
    if not_found_tickets:
        message_parts.append(f"{len(not_found_tickets)} not found")
    if errors:
        message_parts.append(f"{len(errors)} error(s)")
    
    message = ", ".join(message_parts) if message_parts else "No changes"

    all_errors_forbidden = bool(errors) and all(
        isinstance(error, dict) and error.get("code") == "forbidden"
        for error in errors
    )

    if not updated_tickets and errors and all_errors_forbidden and not not_found_tickets:
        return jsonify({
            "success": False,
            "message": "Not authorized to update ticket(s)",
            "errors": errors,
            "data": response_data
        }), 403
    
    # Determine success status
    # If all tickets failed to update (not found or errors), return 400
    if not updated_tickets and (not_found_tickets or errors):
        return jsonify({
            "success": False,
            "message": message,
            "errors": errors if errors else None,
            "data": response_data
        }), 400
    
    return ApiResponse.success(
        data=response_data,
        message=message
    )


@ticket_bp.route("/bulk", methods=["DELETE"])
@jwt_required()
# @admin_required
def delete_tickets_bulk():
    """Delete multiple tickets

    Request body:
    {
        "ids": [
            "uuid-string-or-ticket-id",
            "uuid-string-or-ticket-id"
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "deleted": [...],
            "not_found": [...],
            "errors": [...],
            "total_deleted": 2,
            "total_not_found": 1,
            "total_errors": 0
        },
        "message": "2 ticket(s) deleted successfully, 1 not found"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400

    ids = data.get("ids")
    if not ids or not isinstance(ids, list):
        return jsonify({
            "success": False,
            "message": "ids array is required",
            "errors": None
        }), 400

    current_user = get_current_user()
    if not current_user:
        return jsonify({
            "success": False,
            "message": "User not found",
            "errors": None
        }), 404

    deleted_tickets, not_found_tickets, errors = TicketService.delete_bulk(
        ids=ids,
        current_user_id=str(current_user.id),
        current_user_role=current_user.authorize_role
    )

    response_data = {
        "deleted": deleted_tickets,
        "total_deleted": len(deleted_tickets)
    }

    if not_found_tickets:
        response_data["not_found"] = not_found_tickets
        response_data["total_not_found"] = len(not_found_tickets)

    if errors:
        response_data["errors"] = errors
        response_data["total_errors"] = len(errors)

    message_parts = []
    if deleted_tickets:
        message_parts.append(f"{len(deleted_tickets)} ticket(s) deleted successfully")
    if not_found_tickets:
        message_parts.append(f"{len(not_found_tickets)} not found")
    if errors:
        message_parts.append(f"{len(errors)} error(s)")

    message = ", ".join(message_parts) if message_parts else "No changes"

    all_errors_forbidden = bool(errors) and all(
        isinstance(error, dict) and error.get("code") == "forbidden"
        for error in errors
    )

    if not deleted_tickets and errors and all_errors_forbidden and not not_found_tickets:
        return jsonify({
            "success": False,
            "message": "Not authorized to delete ticket(s)",
            "errors": errors,
            "data": response_data
        }), 403

    if not deleted_tickets and (not_found_tickets or errors):
        return jsonify({
            "success": False,
            "message": message,
            "errors": errors if errors else None,
            "data": response_data
        }), 400

    return ApiResponse.success(
        data=response_data,
        message=message
    )


@ticket_bp.route("/<string:id>", methods=["DELETE"])
@jwt_required()
# @admin_required
def delete_ticket(id: str):
    """Delete ticket"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({
            "success": False,
            "message": "User not found",
            "errors": None
        }), 404

    success, errors = TicketService.delete(
        id=id,
        current_user_id=str(current_user.id),
        current_user_role=current_user.authorize_role
    )
    
    if not success:
        status_code = 404
        if errors and any("not authorized" in err.lower() for err in errors):
            status_code = 403
        elif errors and any("not found" in err.lower() for err in errors):
            status_code = 404
        else:
            status_code = 400

        return jsonify({
            "success": False,
            "message": "Failed to delete ticket",
            "errors": errors
        }), status_code
    
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