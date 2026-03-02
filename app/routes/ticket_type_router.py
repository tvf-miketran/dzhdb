

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.ticket_type_service import TicketTypeService
from app.responses import ApiResponse
from app.utils.decorators import admin_required

ticket_type_bp = Blueprint("ticket_type", __name__)


@ticket_type_bp.route("", methods=["GET"])
@jwt_required()
def get_all_ticket_types():
    """Get all ticket types"""
    ticket_types = TicketTypeService.get_all()
    
    data = [
        {
            "id": str(t.id),
            "typeId": t.type_id,
            "name": t.name
        }
        for t in ticket_types
    ]
    
    return ApiResponse.success(data=data, message="Ticket types retrieved successfully")


@ticket_type_bp.route("/<string:id>", methods=["GET"])
@jwt_required()
def get_ticket_type(id: str):
    """Get ticket type by ID"""
    ticket_type = TicketTypeService.get_by_id(id)
    
    if not ticket_type:
        return jsonify({
            "success": False,
            "message": "Ticket type not found",
            "errors": None
        }), 404
    
    data = {
        "id": str(ticket_type.id),
        "typeId": ticket_type.type_id,
        "name": ticket_type.name
    }
    
    return ApiResponse.success(data=data, message="Ticket type retrieved successfully")


@ticket_type_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_ticket_type():
    """Create new ticket type (Admin only)
    
    Request body:
    {
        "typeId": "BUG",
        "name": "Bug Report"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    type_id = data.get("typeId", "").strip()
    name = data.get("name", "").strip()
    
    if not type_id:
        return jsonify({
            "success": False,
            "message": "typeId is required",
            "errors": None
        }), 400
    
    if not name:
        return jsonify({
            "success": False,
            "message": "name is required",
            "errors": None
        }), 400
    
    ticket_type, errors = TicketTypeService.create(
        type_id=type_id,
        name=name
    )
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Failed to create ticket type",
            "errors": errors
        }), 400
    
    response_data = {
        "id": str(ticket_type.id),
        "typeId": ticket_type.type_id,
        "name": ticket_type.name
    }
    
    return ApiResponse.success(
        data=response_data,
        message="Ticket type created successfully",
        status_code=201
    )


@ticket_type_bp.route("/bulk", methods=["POST"])
@jwt_required()
@admin_required
def create_ticket_types_bulk():
    """Create multiple ticket types (Admin only)
    
    Request body:
    {
        "ticketTypes": [
            {
                "typeId": "BUG",
                "name": "Bug Report"
            },
            {
                "typeId": "FEATURE",
                "name": "Feature Request"
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
    
    ticket_types_data = data.get("ticketTypes", [])
    
    if not ticket_types_data:
        return jsonify({
            "success": False,
            "message": "ticketTypes array is required",
            "errors": None
        }), 400
    
    result, errors = TicketTypeService.create_multiple(ticket_types_data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Failed to create ticket types",
            "errors": errors
        }), 400
    
    return ApiResponse.success(
        data={"ticketTypes": result, "count": len(result)},
        message=f"Successfully created {len(result)} ticket type(s)",
        status_code=201
    )


@ticket_type_bp.route("/<string:id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_ticket_type(id: str):
    """Delete ticket type (Admin only)"""
    success, errors = TicketTypeService.delete(id)
    
    if not success:
        return jsonify({
            "success": False,
            "message": "Failed to delete ticket type",
            "errors": errors
        }), 404
    
    return ApiResponse.success(data=None, message="Ticket type deleted successfully")