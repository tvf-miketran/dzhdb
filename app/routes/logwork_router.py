from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.requests.logwork_request import CreateLogworkRequest, UpdateLogworkRequest
from app.services.logwork_service import LogworkService
from app.responses import ApiResponse
from app.utils.auth_helpers import get_current_user
from app.utils.decorators import admin_required

logwork_bp = Blueprint("logwork", __name__)


def format_month_param(month: str = None) -> str:
    """Convert month parameter to zero-padded format (1 -> 01, 10 -> 10)"""
    if not month:
        return None
    try:
        month_int = int(month)
        if month_int < 1 or month_int > 12:
            return None
        return str(month_int).zfill(2)
    except (ValueError, TypeError):
        return None


@logwork_bp.route("", methods=["GET"])
@jwt_required()
def get_all_logworks():
    """Get all logworks for the current user
    
    Query parameters:
    - month: Filter by single month (optional)
    - quarter: Filter by quarter 1-4 (3 months), optional
    - year: Filter by year (optional)
    - sortBy: Sort by loghours ('asc' or 'desc'), default is by created date (optional)
    """
    user = get_current_user()
    if not user:
        return ApiResponse.error(
            message="User not found",
            errors=["Unable to identify current user"],
            status_code=404
        )
    
    month = format_month_param(request.args.get('month', None))
    quarter = request.args.get('quarter', None)
    year = request.args.get('year', None)
    sort_by = request.args.get('sortBy', None)
    logworks = LogworkService.get_by_user_id_with_month_filter(str(user.id), month=month, quarter=quarter, year=year, sort_by=sort_by)
    data = [LogworkService._to_dict(logwork) for logwork in logworks]
    
    return ApiResponse.success(
        data=data,
        message="Logworks retrieved successfully",
        status_code=200
    )


@logwork_bp.route("/admin/all", methods=["GET"])
@jwt_required()
@admin_required
def get_all_logworks_admin():
    """Get all logworks for all users (Admin only)
    
    Query parameters:
    - month: Filter by single month (optional)
    - quarter: Filter by quarter 1-4 (3 months), optional
    - year: Filter by year (optional)
    - userName: Filter by employee English name (optional, case-insensitive)
    - sortBy: Sort by loghours ('asc' or 'desc'), default is by created date (optional)
    """
    month = format_month_param(request.args.get('month', None))
    quarter = request.args.get('quarter', None)
    year = request.args.get('year', None)
    user_eng_name = request.args.get('userName', None)
    sort_by = request.args.get('sortBy', None)
    
    logworks = LogworkService.get_all_with_filters(month=month, quarter=quarter, year=year, user_eng_name=user_eng_name, sort_by=sort_by)
    data = [LogworkService._to_dict(logwork) for logwork in logworks]
    
    return ApiResponse.success(
        data=data,
        message="All logworks retrieved successfully",
        status_code=200
    )


@logwork_bp.route("/<logwork_id>", methods=["GET"])
@jwt_required()
def get_logwork(logwork_id: str):
    """Get a specific logwork by ID (employees can view their own, admin can view all)"""
    user = get_current_user()
    if not user:
        return ApiResponse.error(
            message="User not found",
            errors=["Unable to identify current user"],
            status_code=404
        )
    
    logwork = LogworkService.get_by_id(logwork_id)
    if not logwork:
        return ApiResponse.error(
            message="Logwork not found",
            errors=[f"No logwork found with ID '{logwork_id}'"],
            status_code=404
        )
    
    # Check authorization: allow if user is admin or if logwork belongs to current user
    if not user.is_admin and str(logwork.user_id) != str(user.id):
        return ApiResponse.error(
            message="Unauthorized",
            errors=["You can only view your own logwork"],
            status_code=403
        )
    
    data = LogworkService._to_dict(logwork)
    return ApiResponse.success(
        data=data,
        message="Logwork retrieved successfully",
        status_code=200
    )


@logwork_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
def create_logwork():
    """Create one or more logworks (Admin only)
    
    Request body (array):
    [
        {
            "userId": "user-uuid",
            "logHour": 160,
            "month": "2",
            "year": "2026"  (optional, defaults to 2026)
        },
        ...
    ]
    """
    # Parse request body
    data = request.get_json()
    if not data:
        return ApiResponse.error(
            message="Invalid request",
            errors=["Request body is required"],
            status_code=400
        )
    
    # Handle array of logworks
    if not isinstance(data, list):
        return ApiResponse.error(
            message="Invalid request",
            errors=["Request body must be an array of logwork objects"],
            status_code=400
        )
    
    if len(data) == 0:
        return ApiResponse.error(
            message="Invalid request",
            errors=["Request body cannot be empty"],
            status_code=400
        )
    
    results = []
    all_errors = []
    
    for idx, item in enumerate(data):
        # Validate request
        create_request, errors = CreateLogworkRequest.from_dict(item)
        if errors:
            all_errors.append({
                "index": idx,
                "errors": errors
            })
            continue
        
        # Create logwork
        logwork, errors = LogworkService.create(create_request)
        if errors:
            all_errors.append({
                "index": idx,
                "errors": errors
            })
            continue
        
        results.append(LogworkService._to_dict(logwork))
    
    # If all failed, return error
    if len(results) == 0:
        return ApiResponse.error(
            message="Failed to create logworks",
            errors=all_errors,
            status_code=400
        )
    
    # If some failed, return partial success with warnings
    if len(all_errors) > 0:
        return ApiResponse.success(
            data=results,
            message=f"Created {len(results)} out of {len(data)} logworks",
            status_code=207
        )
    
    return ApiResponse.success(
        data=results,
        message="Logworks created successfully",
        status_code=201
    )


@logwork_bp.route("/<logwork_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_logwork(logwork_id: str):
    """Update an existing logwork (Admin only)
    
    Request body (all fields optional):
    {
        "logHour": 160,
        "month": "2",
        "year": "2026"
    }
    """
    user = get_current_user()
    if not user:
        return ApiResponse.error(
            message="User not found",
            errors=["Unable to identify current user"],
            status_code=404
        )
    
    # Parse request body
    data = request.get_json()
    if not data:
        return ApiResponse.error(
            message="Invalid request",
            errors=["Request body is required"],
            status_code=400
        )
    
    # Validate request
    update_request, errors = UpdateLogworkRequest.from_dict(data)
    if errors:
        return ApiResponse.error(
            message="Validation failed",
            errors=errors,
            status_code=400
        )
    
    # Update logwork
    logwork, errors = LogworkService.update(logwork_id, str(user.id), update_request)
    if errors:
        return ApiResponse.error(
            message="Failed to update logwork",
            errors=errors,
            status_code=400
        )
    
    result = LogworkService._to_dict(logwork)
    return ApiResponse.success(
        data=result,
        message="Logwork updated successfully",
        status_code=200
    )


@logwork_bp.route("/<logwork_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_logwork(logwork_id: str):
    """Delete a logwork (Admin only)"""
    user = get_current_user()
    if not user:
        return ApiResponse.error(
            message="User not found",
            errors=["Unable to identify current user"],
            status_code=404
        )
    
    # Delete logwork
    success, errors = LogworkService.delete(logwork_id, str(user.id))
    if not success:
        return ApiResponse.error(
            message="Failed to delete logwork",
            errors=errors,
            status_code=400
        )
    
    return ApiResponse.success(
        data=None,
        message="Logwork deleted successfully",
        status_code=200
    )