from typing import Any, Optional, Tuple, Dict


class ApiResponse:
    """Standard API Response wrapper for Flask-RESTX"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200
    ) -> Tuple[Dict, int]:
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        return response, status_code

