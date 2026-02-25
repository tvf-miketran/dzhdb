from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.role_service import RoleService
from app.responses import ApiResponse
from app.utils.decorators import admin_required

role_bp = Blueprint("role", __name__)


@role_bp.route("", methods=["GET"])
@jwt_required()
def get_all_roles():
    """Get all roles 
    """
    roles = RoleService.get_all()
    data = [
        {
            "roleUuid": str(role.id),
            "roleName": role.name,
            "roleId": role.role_id
        }
        for role in roles
    ]
    return ApiResponse.success(data=data, message="Roles retrieved successfully")
    
    # Get filtered and sorted paginated results
    result = RoleService.get_all()
    
    return ApiResponse.success(data=result, message="Roles retrieved successfully")
