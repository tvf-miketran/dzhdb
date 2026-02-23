from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.requests.bank_request import CreateBankRequest, UpdateBankRequest
from app.services.bank_service import BankService
from app.responses import ApiResponse
from app.utils.decorators import admin_required

bank_bp = Blueprint("bank", __name__)


@bank_bp.route("", methods=["GET"])
@jwt_required()
def get_all_banks():
    """Get all banks with pagination, filtering, and sorting
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - search: Search by name
    - sort_by: Sort field (created_at, name)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    # Get pagination params
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Get filter params
    search = request.args.get("search", type=str)
    
    # Get sort params
    sort_by = request.args.get("sort_by", "created_at", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)
    
    # If no pagination, return all (legacy support)
    if not page:
        banks = BankService.get_all()
        data = [
            {
                "id": str(bank.id),
                "name": bank.name,
                "createdAt": bank.created_at.isoformat() if bank.created_at else None
            }
            for bank in banks
        ]
        return ApiResponse.success(data=data, message="Banks retrieved successfully")
    
    # Get filtered and sorted paginated results
    result = BankService.get_all_filtered_sorted(
        page=page,
        per_page=per_page,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return ApiResponse.success(data=result, message="Banks retrieved successfully")


@bank_bp.route("/<string:id>", methods=["GET"])
@jwt_required()
def get_bank(id: str):
    """Get bank by ID
    
    Query parameters:
    - include_projects: Include bank projects (true/false, default: false)
    """
    # Get include_projects param
    include_projects = request.args.get("include_projects", "false", type=str).lower() == "true"
    
    bank = BankService.get_by_id(id)
    
    if not bank:
        return jsonify({
            "success": False,
            "message": "Bank not found",
            "errors": None
        }), 404
    
    data = BankService._to_dict(bank, include_projects=include_projects)
    
    return ApiResponse.success(data=data, message="Bank retrieved successfully")


@bank_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_bank():
    """Create new bank (Admin only)
    
    Request body:
    {
        "name": "Vietcombank"
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
    req, errors = CreateBankRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Create bank
    bank, create_errors = BankService.create(name=req.name)
    
    if create_errors:
        return jsonify({
            "success": False,
            "message": "Failed to create bank",
            "errors": create_errors
        }), 400
    
    response_data = BankService._to_dict(bank)
    
    return ApiResponse.success(
        data=response_data,
        message="Bank created successfully",
        status_code=201
    )


@bank_bp.route("/<string:id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_bank(id: str):
    """Update bank (Admin only)
    
    Request body:
    {
        "name": "Updated Bank Name"
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
    req, errors = UpdateBankRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Update bank
    bank, update_errors = BankService.update(id=id, name=req.name)
    
    if update_errors:
        status_code = 404 if "not found" in update_errors[0].lower() else 400
        return jsonify({
            "success": False,
            "message": update_errors[0],
            "errors": update_errors
        }), status_code
    
    response_data = BankService._to_dict(bank)
    
    return ApiResponse.success(data=response_data, message="Bank updated successfully")


@bank_bp.route("/<string:id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_bank(id: str):
    """Delete bank (Admin only)
    
    Note: This will set bank_id to NULL for all related projects
    """
    success, error = BankService.delete(id)
    
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({
            "success": False,
            "message": error,
            "errors": None
        }), status_code
    
    return ApiResponse.success(data=None, message="Bank deleted successfully")