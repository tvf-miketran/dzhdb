from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.requests.project_request import AddProjectMembersRequest, CreateProjectRequest, UpdateProjectRequest, RemoveProjectMembersRequest
from app.services.project_service import ProjectService
from app.responses import ApiResponse
from app.utils.decorators import admin_required

project_bp = Blueprint("project", __name__)


@project_bp.route("", methods=["GET"])
@jwt_required()
def get_all_projects():
    """Get all projects with pagination, filtering, and sorting
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - bank_id: Filter by bank UUID
    - search: Search by name, pm_name, or project_id
    - sort_by: Sort field (created_at, name, pm_name, project_id)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    # Get pagination params
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Get filter params
    bank_id = request.args.get("bank_id", type=str)
    search = request.args.get("search", type=str)
    
    # Get sort params
    sort_by = request.args.get("sort_by", "created_at", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)
    
    # If no pagination, return all (legacy support)
    if not page:
        projects = ProjectService.get_all()
        data = [
            {
                "id": str(proj.id),
                "projectId": proj.project_id,
                "name": proj.name,
                "pmName": proj.pm_name,
                "projectLink": proj.project_link,
                "bankId": str(proj.bank_id) if proj.bank_id else None,
                "bankName": proj.bank.name if proj.bank else None,
                "createdAt": proj.created_at.isoformat() if proj.created_at else None,
                "startDate": proj.start_date.isoformat() if proj.start_date else None,
                "endDate": proj.end_date.isoformat() if proj.end_date else None
            }
            for proj in projects
        ]
        return ApiResponse.success(data=data, message="Projects retrieved successfully")
    
    # Get filtered and sorted paginated results
    result = ProjectService.get_all_filtered_sorted(
        page=page,
        per_page=per_page,
        bank_id=bank_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return ApiResponse.success(data=result, message="Projects retrieved successfully")


@project_bp.route("/<string:id>", methods=["GET"])
@jwt_required()
def get_project(id: str):
    """Get project by ID (UUID or project_id)
    
    Query parameters:
    - include_members: Include project members (true/false, default: true)
    """
    # Get include_members param (default true for detail endpoint)
    include_members = request.args.get("include_members", "true", type=str).lower() == "true"
    
    # Try to get by UUID first
    project = ProjectService.get_by_id(id)
    
    if not project:
        return jsonify({
            "success": False,
            "message": "Project not found",
            "errors": None
        }), 404
    
    data = ProjectService._to_dict(project, include_members=include_members)
    
    return ApiResponse.success(data=data, message="Project retrieved successfully")

@project_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_project():
    """Create new project (Admin only)
    
    Request body:
    {
        "name": "Project Name",
        "pmName": "PM Full Name",
        "projectId": "PROJ001",
        "bankId": "uuid-string" (optional),
        "projectLink": "https://..." (optional),
        "startDate": "24022026" (optional, DDMMYYYY format),
        "endDate": "31122026" (optional, DDMMYYYY format)
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
    req, errors = CreateProjectRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Create project
    project, create_errors = ProjectService.create(
        name=req.name,
        pm_name=req.pm_name,
        project_id=req.project_id,
        bank_id=req.bank_id,
        project_link=req.project_link,
        start_date=req.start_date,
        end_date=req.end_date
    )
    
    if create_errors:
        return jsonify({
            "success": False,
            "message": "Failed to create project",
            "errors": create_errors
        }), 400
    
    response_data = ProjectService._to_dict(project)
    
    return ApiResponse.success(
        data=response_data,
        message="Project created successfully",
        status_code=201
    )


@project_bp.route("/<string:id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_project(id: str):
    """Update project (Admin only)
    
    Request body:
    {
        "name": "Updated Project Name" (optional),
        "pmName": "Updated PM Name" (optional),
        "projectId": "PROJ002" (optional),
        "bankId": "uuid-string" (optional),
        "projectLink": "https://..." (optional),
        "startDate": "24022026" (optional, DDMMYYYY format),
        "endDate": "31122026" (optional, DDMMYYYY format)
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
    req, errors = UpdateProjectRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Update project
    project, update_errors = ProjectService.update(
        id=id,
        name=req.name,
        pm_name=req.pm_name,
        project_id=req.project_id,
        bank_id=req.bank_id,
        project_link=req.project_link,
        start_date=req.start_date,
        end_date=req.end_date
    )
    
    if update_errors:
        status_code = 404 if "not found" in update_errors[0].lower() else 400
        return jsonify({
            "success": False,
            "message": update_errors[0],
            "errors": update_errors
        }), status_code
    
    response_data = ProjectService._to_dict(project, include_members=True)
    
    return ApiResponse.success(data=response_data, message="Project updated successfully")


@project_bp.route("/<string:id>/members", methods=["POST"])
@jwt_required()
@admin_required
def add_project_members(id: str):
    """Add members to project (Admin only)
    
    Request body:
    {
        "members": [
            {
                "userId": "uuid-string" OR "employeeId": "T0759",
                "allocationPercent": 50,
                "roleId": "uuid-string" (optional)
            },
            {
                "employeeId": "T0760",
                "allocationPercent": 100,
                "roleId": "uuid-string" (optional)
            }
        ]
    }
    
    Note: 
    - You can use either userId (UUID) or employeeId (e.g., T0759)
    - allocationPercent must be between 0 and 100
    - roleId is optional and must be a valid role UUID or role name
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required",
            "errors": None
        }), 400
    
    # Validate request
    req, errors = AddProjectMembersRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Add members
    members, add_errors = ProjectService.add_members(
        project_id=id,
        members=req.members
    )
    
    if add_errors:
        status_code = 404 if "not found" in add_errors[0].lower() else 400
        return jsonify({
            "success": False,
            "message": "Failed to add members",
            "errors": add_errors
        }), status_code
    
    return ApiResponse.success(
        data={"members": members, "count": len(members)},
        message=f"Successfully added/updated {len(members)} member(s)",
        status_code=201
    )


@project_bp.route("/<string:id>/members", methods=["DELETE"])
@jwt_required()
@admin_required
def remove_project_members(id: str):
    """Remove members from project (Admin only)
    
    Request body:
    {
        "members": [
            {
                "userId": "uuid-string"
            },
            {
                "userId": "uuid-string"
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
    
    # Validate request
    req, errors = RemoveProjectMembersRequest.from_dict(data)
    
    if errors:
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": errors
        }), 422
    
    # Remove members
    result, remove_errors = ProjectService.remove_members(
        project_id=id,
        members=req.members
    )
    
    if result is None:
        # Complete failure (e.g., project not found)
        return jsonify({
            "success": False,
            "message": "Failed to remove members",
            "errors": remove_errors
        }), 404
    
    # Partial or complete success
    removed_count = result['removedCount']
    failed_count = result['failedCount']
    
    if removed_count > 0:
        # At least some members were removed - return success
        message = f"Successfully removed {removed_count} member(s)"
        if failed_count > 0:
            message += f", {failed_count} member(s) failed"
        
        return ApiResponse.success(
            data=result,
            message=message,
            errors=remove_errors
        )
    else:
        # No members were removed - return failure
        return jsonify({
            "success": False,
            "message": "Failed to remove members",
            "errors": remove_errors
        }), 400
