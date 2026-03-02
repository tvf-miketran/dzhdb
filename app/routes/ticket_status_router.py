

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.ticket_status_service import TicketStatusService
from app.responses import ApiResponse
from app.utils.decorators import admin_required

ticket_status_bp = Blueprint("ticket_status", __name__)


@ticket_status_bp.route("", methods=["GET"])
@jwt_required()
def get_all_ticket_statuses():
    """Get all ticket statuses"""
    ticket_statuses = TicketStatusService.get_all()
    
    data = [
        {
            "id": str(t.id),
            "statusId": t.status_id,
            "name": t.name
        }
        for t in ticket_statuses
    ]
    
    return ApiResponse.success(data=data, message="Ticket statuses retrieved successfully")


@ticket_status_bp.route("/<string:id>", methods=["GET"])
@jwt_required()
def get_ticket_status(id: str):
    """Get ticket status by ID"""
    ticket_status = TicketStatusService.get_by_id(id)
    
    if not ticket_status:
        return jsonify({
            "success": False,
            "message": "Ticket status not found",
            "errors": None
        }), 404
    
    data = {
        "id": str(ticket_status.id),
        "statusId": ticket_status.status_id,
        "name": ticket_status.name
    }
    
    return ApiResponse.success(data=data, message="Ticket status retrieved successfully")


@ticket_status_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_ticket_status():
    """Create new ticket status (Admin only)
    
    Request body:
    {
        "statusId": "OPEN",
        "name": "Open"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    status_id = data.get("statusId", "").strip()
    name = data.get("name", "").strip()
    
    if not status_id:
        return jsonify({
            "success": False,
            "message": "statusId is required",
            "errors": None
        }), 400
    
    if not name:
        return jsonify({
            "success": False,
            "message": "name is required",
            "errors": None
        }), 400
    
    ticket_status, errors = TicketStatusService.create(
        status_id=status_id,
        name=name
    )
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Failed to create ticket status",
            "errors": errors
        }), 400
    
    response_data = {
        "id": str(ticket_status.id),
        "statusId": ticket_status.status_id,
        "name": ticket_status.name
    }
    
    return ApiResponse.success(
        data=response_data,
        message="Ticket status created successfully",
        status_code=201
    )


@ticket_status_bp.route("/bulk", methods=["POST"])
@jwt_required()
@admin_required
def create_ticket_statuses_bulk():
    """Create multiple ticket statuses (Admin only)
    
    Request body:
    {
        "ticketStatuses": [
            {
                "statusId": "OPEN",
                "name": "Open"
            },
            {
                "statusId": "IN_PROGRESS",
                "name": "In Progress"
            }
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
    
    ticket_statuses_data = data.get("ticketStatuses", [])
    
    if not ticket_statuses_data:
        return jsonify({
            "success": False,
            "message": "ticketStatuses array is required",
            "errors": None
        }), 400
    
    result, errors = TicketStatusService.create_multiple(ticket_statuses_data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Failed to create ticket statuses",
            "errors": errors
        }), 400
    
    return ApiResponse.success(
        data={"ticketStatuses": result, "count": len(result)},
        message=f"Successfully created {len(result)} ticket status(es)",
        status_code=201
    )


@ticket_status_bp.route("/<string:id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_ticket_status(id: str):
    """Delete ticket status (Admin only)"""
    success, errors = TicketStatusService.delete(id)
    
    if not success:
        return jsonify({
            "success": False,
            "message": "Failed to delete ticket status",
            "errors": errors
        }), 404
    
    return ApiResponse.success(data=None, message="Ticket status deleted successfully")


