from typing import Any, Optional, List


class ApiException(Exception):
    """Base API Exception"""
    status_code: int = 500
    message: str = "An error occurred"
    errors: Optional[Any] = None

    def __init__(self, message: str = None, errors: Any = None, status_code: int = None):
        self.message = message or self.__class__.message
        self.errors = errors
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self):
        return {
            "success": False,
            "message": self.message,
            "errors": self.errors
        }


class BadRequestException(ApiException):
    status_code = 400
    message = "Bad request"


class UnauthorizedException(ApiException):
    status_code = 401
    message = "Unauthorized"


class ForbiddenException(ApiException):
    status_code = 403
    message = "Forbidden"


class NotFoundException(ApiException):
    status_code = 404
    message = "Resource not found"


class ValidationException(ApiException):
    status_code = 422
    message = "Validation failed"

    def __init__(self, errors: List[str], message: str = "Validation failed"):
        super().__init__(message=message, errors=errors)


class InternalServerException(ApiException):
    status_code = 500
    message = "Internal server error"