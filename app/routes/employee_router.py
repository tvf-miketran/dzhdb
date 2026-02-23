from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.employee_service import EmployeeService
from app.requests.employee_request import CreateEmployeeRequest, UpdateEmployeeRequest
from app.utils.decorators import admin_required
from app.responses import ApiResponse

employee_bp = Blueprint("employee", __name__)


@employee_bp.route("", methods=["GET"])
@jwt_required()
def get_all_employees():
    """Get all employees with pagination, filtering, and sorting
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - status: Filter by status (true or false)
    - search: Search by name, email, or employeeId
    - sort_by: Sort field (created_at, updated_at, vn_full_name, en_full_name, email, employeeId, status)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    # Get pagination params
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Get filter params
    status_param = request.args.get("status", type=str)
    search = request.args.get("search", type=str)
    
    # Get sort params
    sort_by = request.args.get("sort_by", "created_at", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)
    
    # Convert status string to boolean
    status = None
    if status_param:
        if status_param.lower() == "true":
            status = True
        elif status_param.lower() == "false":
            status = False
    
    # If no pagination, return all (legacy support)
    if not page:
        employees = EmployeeService.get_all()
        data = [
            {
                "id": str(emp.id),
                "employeeId": emp.employeeId,
                "email": emp.email,
                "vnFullName": emp.vn_full_name,
                "enFullName": emp.en_full_name,
                "description": emp.description,
                "authorizeRole": emp.authorize_role,
                "status": emp.status,
                "createdAt": emp.created_at.isoformat() if emp.created_at else None,
                "updatedAt": emp.updated_at.isoformat() if emp.updated_at else None
            }
            for emp in employees
        ]
        return ApiResponse.success(data=data, message="Employees retrieved successfully")
    
    # Get filtered and sorted paginated results
    result = EmployeeService.get_all_filtered_sorted(
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return ApiResponse.success(data=result, message="Employees retrieved successfully")


@employee_bp.route("/<string:id>", methods=["GET"])
@jwt_required()
def get_employee(id: str):
    """Get employee by ID (UUID or employeeId)"""
    # Try to get by UUID first
    employee = EmployeeService.get_by_id(id)
    
    # If not found, try by employeeId
    if not employee:
        employee = EmployeeService.get_by_employee_id(id)
    
    if not employee:
        return jsonify({
            "success": False,
            "message": "Employee not found",
            "errors": None
        }), 404
    
    data = {
        "id": str(employee.id),
        "employeeId": employee.employeeId,
        "email": employee.email,
        "vnFullName": employee.vn_full_name,
        "enFullName": employee.en_full_name,
        "authorizeRole": employee.authorize_role,
        "description": employee.description,
        "status": employee.status,
        "createdAt": employee.created_at.isoformat() if employee.created_at else None,
        "updatedAt": employee.updated_at.isoformat() if employee.updated_at else None
    }
    
    return ApiResponse.success(data=data, message="Employee retrieved successfully")


@employee_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_employee():
    """Create new employee (Admin only)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    # Validate request
    req, errors = CreateEmployeeRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Create employee
    employee, create_errors = EmployeeService.create(
        employee_id=req.employee_id,
        email=req.email,
        password=req.password,
        vn_full_name=req.vn_full_name,
        en_full_name=req.en_full_name,
        description=req.description,
        authorize_role=req.authorize_role,
        status=req.status
    )
    
    if create_errors:
        return jsonify({
            "success": False,
            "message": "Failed to create employee",
            "errors": create_errors
        }), 400
    
    response_data = {
        "id": str(employee.id),
        "employeeId": employee.employeeId,
        "vnFullName": employee.vn_full_name,
        "enFullName": employee.en_full_name,
        "email": employee.email,
        "description": employee.description,
        "authorizeRole": employee.authorize_role,
        "status": employee.status,
        "createdAt": employee.created_at.isoformat() if employee.created_at else None
    }
    
    return ApiResponse.success(data=response_data, message="Employee created successfully", status_code=201)


@employee_bp.route("/<string:id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_employee(id: str):
    """Update employee (Admin only)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    # Validate request
    req, errors = UpdateEmployeeRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Update employee
    employee, update_errors = EmployeeService.update(
        id=id,
        vn_full_name=req.vn_full_name,
        en_full_name=req.en_full_name,
        email=req.email,
        employee_id=req.employee_id,
        description=req.description,
        authorize_role=req.authorize_role,
        status=req.status
    )
    
    if update_errors:
        status_code = 404 if "not found" in update_errors[0].lower() else 400
        return jsonify({
            "success": False,
            "message": update_errors[0],
            "errors": update_errors
        }), status_code
    
    data = {
        "id": str(employee.id),
        "employeeId": employee.employeeId,
        "email": employee.email,
        "vnFullName": employee.vn_full_name,
        "enFullName": employee.en_full_name,
        "description": employee.description,
        "authorizeRole": employee.authorize_role,
        "status": employee.status,
        "updatedAt": employee.updated_at.isoformat() if employee.updated_at else None
    }
    
    return ApiResponse.success(data=data, message="Employee updated successfully")

@employee_bp.route("/reset-password", methods=["POST"])
@jwt_required()
@admin_required
def reset_password():
    """Reset employee password to their email (Admin only)
    
    Request body:
    {
        "employeeId": "T0759"
    }
    
    Response:
    {
        "success": true,
        "message": "Password reset successfully. New password is the employee's email.",
        "data": null
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    employee_id = data.get("employeeId")
    
    if not employee_id:
        return jsonify({
            "success": False,
            "message": "Employee ID is required",
            "errors": ["employeeId field is required"]
        }), 400
    
    success = EmployeeService.reset_password_to_email(employee_id)
    
    if not success:
        return jsonify({
            "success": False,
            "message": "Employee not found",
            "errors": None
        }), 404
    
    return ApiResponse.success(
        data=None,
        message="Password reset successfully. New password is the employee's email."
    )

@employee_bp.route("/<string:id>/toggle-status", methods=["PATCH"])
@jwt_required()
@admin_required
def toggle_employee_status(id: str):
    """Toggle employee status between active and inactive (Admin only)"""
    employee, error = EmployeeService.toggle_status(id)
    
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({
            "success": False,
            "message": error,
            "errors": None
        }), status_code
    
    data = {
        "id": str(employee.id),
        "employeeId": employee.employeeId,
        "email": employee.email,
        "vnFullName": employee.vn_full_name,
        "enFullName": employee.en_full_name,
        "description": employee.description,
        "authorizeRole": employee.authorize_role,
        "status": employee.status,
        "updatedAt": employee.updated_at.isoformat() if employee.updated_at else None
    }
    
    status_text = "activated" if employee.status else "deactivated"
    return ApiResponse.success(data=data, message=f"Employee {status_text} successfully")


@employee_bp.route("/<string:id>/status", methods=["PATCH"])
@jwt_required()
@admin_required
def set_employee_status(id: str):
    """Set employee status explicitly (Admin only)
    
    Request body:
    {
        "status": true  // true for active, false for inactive
    }
    """
    data = request.get_json()
    
    if not data or "status" not in data:
        return jsonify({
            "success": False,
            "message": "Status field is required",
            "errors": ["status field must be provided"]
        }), 400
    
    status = data.get("status")
    
    if not isinstance(status, bool):
        return jsonify({
            "success": False,
            "message": "Invalid status value",
            "errors": ["status must be a boolean (true/false)"]
        }), 422
    
    employee, error = EmployeeService.set_status(id, status)
    
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({
            "success": False,
            "message": error,
            "errors": None
        }), status_code
    
    response_data = {
        "id": str(employee.id),
        "employeeId": employee.employeeId,
        "email": employee.email,
        "vnFullName": employee.vn_full_name,
        "enFullName": employee.en_full_name,
        "description": employee.description,
        "authorizeRole": employee.authorize_role,
        "status": employee.status,
        "updatedAt": employee.updated_at.isoformat() if employee.updated_at else None
    }
    
    status_text = "activated" if employee.status else "deactivated"
    return ApiResponse.success(data=response_data, message=f"Employee {status_text} successfully")