from flask import jsonify
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from werkzeug.exceptions import HTTPException

from app.exceptions.http_exceptions import ApiException


def register_error_handlers(app):
    """Register global error handlers for the Flask app"""

    @app.errorhandler(ApiException)
    def handle_api_exception(error: ApiException):
        """Handle custom API exceptions"""
        return error.to_dict(), error.status_code

    @app.errorhandler(NoAuthorizationError)
    def handle_no_authorization(error):
        """Handle missing JWT token"""
        return {
            "success": False,
            "message": "Missing authorization token",
            "errors": None
        }, 401

    @app.errorhandler(InvalidHeaderError)
    def handle_invalid_header(error):
        """Handle invalid JWT header"""
        return {
            "success": False,
            "message": "Invalid authorization header",
            "errors": str(error)
        }, 401

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_token(error):
        """Handle expired JWT token"""
        return {
            "success": False,
            "message": "Token has expired",
            "errors": None
        }, 401

    @app.errorhandler(InvalidTokenError)
    def handle_invalid_token(error):
        """Handle invalid JWT token"""
        return {
            "success": False,
            "message": "Invalid token",
            "errors": str(error)
        }, 401

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """Handle Werkzeug HTTP exceptions (404, 405, etc.)"""
        return {
            "success": False,
            "message": error.description,
            "errors": None
        }, error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        """Handle all other unhandled exceptions"""
        # Log the error for debugging
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        # In production, don't expose error details
        if app.debug:
            return {
                "success": False,
                "message": "Internal server error",
                "errors": str(error)
            }, 500
        else:
            return {
                "success": False,
                "message": "Internal server error",
                "errors": None
            }, 500