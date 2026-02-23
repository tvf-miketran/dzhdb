from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.responses.api_response import ApiResponse
from app.services.auth_service import AuthService
from app.utils.decorators import admin_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = AuthService.login(
        email=email,
        password=password
    )

    if not user:
        return jsonify({"msg": "Bad credentials"}), 401

    return jsonify(user=user)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    employee_id = get_jwt_identity()
    employee = AuthService.get_current_employee(employee_id)

    if not employee:
        return jsonify({"msg": "User not found"}), 404

    return jsonify(
        employeeId=employee.employeeId,
        role=employee.authorize_role
    )

@auth_bp.route("/update-password", methods=["POST"])
@jwt_required()
def update_password():
    data = request.get_json()
    employee_id = get_jwt_identity()

    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    if not old_password or not new_password:
        return jsonify({"msg": "Missing required fields"}), 400

    success = AuthService.update_password(
        employee_id=employee_id,
        old_password=old_password,
        new_password=new_password
    )

    if not success:
        return jsonify({"msg": "Old password is incorrect"}), 400

    return jsonify({"msg": "Password updated successfully"})

@auth_bp.route("/reset-password", methods=["POST"])
@jwt_required()
@admin_required
def reset_password():

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
    
    success = AuthService.reset_password_to_email(employee_id)
    
    if not success:
        return jsonify({
            "success": False,
            "message": "Employee not found",
            "errors": None
        }), 404
    
    return ApiResponse.success(
        data=None,
        message="Password reset successfully"
    )