from datetime import datetime

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required

from app.responses import ApiResponse
from app.services.export_service import ExportService
from app.utils.decorators import admin_required


export_bp = Blueprint("export", __name__)


@export_bp.route("/tables", methods=["GET"])
@jwt_required()
@admin_required
def get_export_tables():
    """Get list of exportable tables for FE filtering."""
    try:
        data = ExportService.get_exportable_tables()
        return ApiResponse.success(data=data, message="Export tables retrieved successfully")
    except Exception as exc:
        return ApiResponse.error(
            message="Failed to get export tables",
            errors=[str(exc)],
            status_code=500,
        )


@export_bp.route("/excel/import", methods=["POST"])
@jwt_required()
@admin_required
def import_excel():
    """Import all table data from excel after cleaning existing business tables."""
    upload_file = request.files.get("file")
    if not upload_file:
        return ApiResponse.error(message="file is required", status_code=400)

    if not upload_file.filename or not upload_file.filename.lower().endswith(".xlsx"):
        return ApiResponse.error(message="file must be .xlsx", status_code=400)

    try:
        result = ExportService.import_database_from_excel(upload_file.stream)
        return ApiResponse.success(data=result, message="Import completed successfully")
    except ValueError as exc:
        return ApiResponse.error(message=str(exc), status_code=400)
    except Exception as exc:
        return ApiResponse.error(
            message="Failed to import excel",
            errors=[str(exc)],
            status_code=500,
        )


@export_bp.route("/excel/export", methods=["POST"])
@jwt_required()
@admin_required
def export_excel():
    """Export all database tables except migration tables to an Excel file."""

    try:
        file_buffer, metadata = ExportService.export_database_to_excel()
    except ValueError as exc:
        return ApiResponse.error(message=str(exc), status_code=400)
    except Exception as exc:
        return ApiResponse.error(
            message="Failed to export excel",
            errors=[str(exc)],
            status_code=500,
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"db_export_{timestamp}.xlsx"

    response = send_file(
        file_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.headers["X-Export-Table-Count"] = str(metadata.get("table_count", 0))
    return response
