from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.requests.logwork_request import CreateLogworkRequest
from app.services.logwork_service import LogworkService
from app.responses import ApiResponse
from app.utils.auth_helpers import get_current_user
from app.utils.decorators import admin_required
from app.utils.query_helpers import parse_month_list_param

logwork_bp = Blueprint("logwork", __name__)


@logwork_bp.route("", methods=["GET"])
@jwt_required()
def get_all_logworks():
    """Get all logworks for the current user

    Query parameters:
    - month: Comma-separated months to filter by e.g. month=1,2,3 (optional)
    - quarter: Filter by quarter 1-4 (3 months), optional
    - year: Filter by year (optional)
    - projectId: Filter by project UUID (optional)
    - sortBy: Sort by loghours ('asc' or 'desc'), default is by created date (optional)
    """
    user = get_current_user()
    if not user:
        return ApiResponse.error(
            message="User not found",
            errors=["Unable to identify current user"],
            status_code=404
        )

    months = parse_month_list_param(request.args.get('month', None))
    quarter = request.args.get('quarter', None)
    year = request.args.get('year', None)
    project_id = request.args.get('projectId', None)
    sort_by = request.args.get('sortBy', None)
    logworks = LogworkService.get_by_user_id_with_month_filter(
        str(user.id), months=months or None, quarter=quarter, year=year, project_id=project_id, sort_by=sort_by
    )
    data = LogworkService.to_member_payload(
        logworks=logworks,
        user_id=str(user.id),
        eng_name=user.en_full_name,
    )

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
    - month: Comma-separated months to filter by e.g. month=1,2,3 (optional)
    - quarter: Filter by quarter 1-4 (3 months), optional
    - year: Filter by year (optional)
    - projectId: Filter by project UUID (optional)
    - userName: Filter by employee English name (optional, case-insensitive)
    - sortBy: Sort by loghours ('asc' or 'desc'), default is by created date (optional)
    """
    months = parse_month_list_param(request.args.get('month', None))
    quarter = request.args.get('quarter', None)
    year = request.args.get('year', None)
    project_id = request.args.get('projectId', None)
    user_eng_name = request.args.get('userName', None)
    sort_by = request.args.get('sortBy', None)

    logworks = LogworkService.get_all_with_filters(
        months=months or None,
        quarter=quarter,
        year=year,
        user_eng_name=user_eng_name,
        project_id=project_id,
        sort_by=sort_by,
    )
    data = LogworkService.to_list_with_metrics(logworks).get("items", [])

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
def upsert_logworks():
    """Create or update logworks (Admin only)

    Accepts an array of logwork objects. For each entry, if a logwork already
    exists for the given (userId, projectId, month, year) it will be updated; otherwise
    a new record is created.

    Request body (array):
    [
        {
            "userId": "user-uuid",
            "projectId": "project-uuid",
            "logHour": 160,
            "month": "2",
            "year": "2026"   (optional, defaults to 2026)
        },
        ...
    ]
    """
    body = request.get_json()
    if not body:
        return ApiResponse.error(
            message="Invalid request",
            errors=["Request body is required"],
            status_code=400
        )

    # Accept { "logworks": [...] }
    if isinstance(body, dict):
        data = body.get("logworks")
        if data is None:
            return ApiResponse.error(
                message="Invalid request",
                errors=['Request body must contain a "logworks" array'],
                status_code=400
            )
    else:
        data = body

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
    deleted_count = 0

    for idx, item in enumerate(data):
        # Validate request
        upsert_request, errors = CreateLogworkRequest.from_dict(item)
        if errors:
            all_errors.append({"index": idx, "errors": errors})
            continue

        # Upsert logwork
        logwork, errors, deleted = LogworkService.upsert(upsert_request)
        if errors:
            all_errors.append({"index": idx, "errors": errors})
            continue

        if deleted:
            deleted_count += 1
            continue

        results.append(LogworkService._to_dict(logwork))

    # If all failed, return error
    if len(results) == 0 and deleted_count == 0:
        return ApiResponse.error(
            message="Failed to upsert logworks",
            errors=all_errors,
            status_code=400
        )

    # If some failed, return partial success with warnings
    if len(all_errors) > 0:
        return ApiResponse.success(
            data=results,
            message=f"Upserted {len(results)} logworks and deleted {deleted_count} logworks out of {len(data)} requests",
            status_code=207
        )

    return ApiResponse.success(
        data=results,
        message=f"Upserted {len(results)} logworks and deleted {deleted_count} logworks successfully",
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