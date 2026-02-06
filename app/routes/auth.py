from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth import AuthService

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    token = AuthService.login(
        employee_id=data.get("employeeId"),
        password=data.get("password")
    )

    if not token:
        return jsonify({"msg": "Bad credentials"}), 401

    return jsonify(access_token=token)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    employee_id = get_jwt_identity()
    employee = AuthService.get_current_employee(employee_id)

    if not employee:
        return jsonify({"msg": "User not found"}), 404

    return jsonify(
        employeeId=employee.employeeId,
        role=employee.role
    )

@auth_bp.route("/reset-password", methods=["POST"])
@jwt_required()
def reset_password():
    data = request.get_json()
    employee_id = get_jwt_identity()

    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    if not old_password or not new_password:
        return jsonify({"msg": "Missing required fields"}), 400

    success = AuthService.reset_password(
        employee_id=employee_id,
        old_password=old_password,
        new_password=new_password
    )

    if not success:
        return jsonify({"msg": "Old password is incorrect"}), 400

    return jsonify({"msg": "Password reset successfully"})