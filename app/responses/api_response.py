from typing import Any, Optional, Tuple, Dict, List


class ApiResponse:
    """Standard API Response wrapper for Flask"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        errors: Optional[List[str]] = None
    ) -> Tuple[Dict, int]:
        """Return a successful response"""
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        if errors:
            response["errors"] = errors
        return response, status_code
    
    @staticmethod
    def error(
        message: str = "Error",
        errors: Optional[List[str]] = None,
        status_code: int = 400
    ) -> Tuple[Dict, int]:
        """Return an error response"""
        response = {
            "success": False,
            "message": message,
            "errors": errors or []
        }
        return response, status_code

