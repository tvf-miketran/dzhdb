from typing import Optional, Dict, Any, List
import json
from datetime import datetime
from app.models.systemparam import SystemParameter
from app import db


class FormulaDAO:
    """DAO for managing formula system parameters in the database"""

    @staticmethod
    def get_current_month() -> int:
        """Get current month number (1-12)"""
        return datetime.now().month

    @staticmethod
    def get_month_prefix(month: int = None) -> str:
        """Get month prefix (e.g., '01', '02', etc.)
        
        Args:
            month: Month number (1-12). If None, uses current month.
            
        Returns:
            Two-digit month string (e.g., '01' for January)
        """
        if month is None:
            month = datetime.now().month
        return str(month).zfill(2)

    @staticmethod
    def get_prefixed_key(param_key: str, month: int = None) -> str:
        """Get month-prefixed key
        
        Args:
            param_key: The base parameter key (e.g., 'DEV_ROLE_WEIGHT')
            month: Month number (1-12). If None, uses current month.
            
        Returns:
            Prefixed key (e.g., '01_DEV_ROLE_WEIGHT')
        """
        prefix = FormulaDAO.get_month_prefix(month)
        return f"{prefix}_{param_key}"

    @staticmethod
    def strip_prefix(param_key: str) -> str:
        """Strip month prefix from key
        
        Args:
            param_key: The prefixed key (e.g., '01_DEV_ROLE_WEIGHT')
            
        Returns:
            Base key (e.g., 'DEV_ROLE_WEIGHT')
        """
        # Check if key starts with month prefix (e.g., '01_', '12_')
        if len(param_key) >= 3 and param_key[2] == '_':
            try:
                # Try to parse as month prefix
                month_num = int(param_key[:2])
                if 1 <= month_num <= 12:
                    return param_key[3:]  # Strip the prefix
            except ValueError:
                pass
        return param_key

    @staticmethod
    def get_param(param_key: str, month: int = None) -> Optional[str]:
        """Get system parameter value by key
        
        Args:
            param_key: The parameter key (base or prefixed)
            month: Month number (1-12). If provided, uses prefixed key.
                   If None, defaults to current month.
                   
        Returns:
            Parameter value or None if not found
        """
        if month is not None:
            param_key = FormulaDAO.get_prefixed_key(param_key, month)
        
        param = SystemParameter.query.filter_by(param_key=param_key).first()
        return param.param_value if param else None

    @staticmethod
    def set_param(param_key: str, param_value: str, month: int = None, description: str = None) -> SystemParameter:
        """Set system parameter value
        
        Args:
            param_key: The parameter key (base or prefixed)
            param_value: The parameter value
            month: Month number (1-12). If provided, stores with prefixed key.
            description: Optional description
        """
        if month is not None:
            param_key = FormulaDAO.get_prefixed_key(param_key, month)
        
        param = SystemParameter.query.filter_by(param_key=param_key).first()
        if param:
            param.param_value = param_value
            if description:
                param.description = description
        else:
            param = SystemParameter(
                param_key=param_key,
                param_value=param_value,
                description=description
            )
            db.session.add(param)
        db.session.commit()
        return param

    @staticmethod
    def get_all_params(month: int = None) -> Dict[str, Optional[str]]:
        """Get all formula parameters
        
        Args:
            month: Month number (1-12). If provided, gets params for that month.
                  If None, defaults to current month.
                  
        Returns:
            Dict of parameter key -> value
        """
        if month is None:
            month = datetime.now().month
        
        prefix = FormulaDAO.get_month_prefix(month)
        
        # Get all params that start with the month prefix and DON'T end with _FORMULA_STRING
        params = SystemParameter.query.filter(
            SystemParameter.param_key.like(f"{prefix}_%"),
            ~SystemParameter.param_key.endswith("_FORMULA_STRING"),
            ~SystemParameter.param_key.endswith("_DATA")
        ).all()
        
        result = {}
        for param in params:
            # Strip the prefix to get base key
            base_key = FormulaDAO.strip_prefix(param.param_key)
            result[base_key] = param.param_value
        
        return result

    @staticmethod
    def get_formulas(month: int = None) -> Dict[str, str]:
        """Get all formula strings
        
        Args:
            month: Month number (1-12). If provided, gets formulas for that month.
                  If None, defaults to current month.
                  
        Returns:
            Dict of formula key -> formula string
        """
        if month is None:
            month = datetime.now().month
        
        prefix = FormulaDAO.get_month_prefix(month)
        
        # Get all params that start with the month prefix and END with _FORMULA_STRING
        formulas = SystemParameter.query.filter(
            SystemParameter.param_key.like(f"{prefix}_%"),
            SystemParameter.param_key.endswith("_FORMULA_STRING")
        ).all()
        
        result = {}
        for param in formulas:
            # Strip the prefix to get base key
            base_key = FormulaDAO.strip_prefix(param.param_key)
            result[base_key] = param.param_value
        
        return result

    @staticmethod
    def is_ticket_formula(formula_key: str) -> bool:
        """Check if formula key is for ticket"""
        return formula_key.startswith("TICKET_")
    
    @staticmethod
    def is_logwork_formula(formula_key: str) -> bool:
        """Check if formula key is for logwork"""
        return formula_key.startswith("LOGWORK_")

    @staticmethod
    def get_calculated_data(month: int, year: int, latest: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Get calculated data from database
        
        Args:
            month: Month number (1-12)
            year: Year (e.g., 2026)
            latest: If False, fetch from stored data. If True, return None to trigger recalculation.
                    
        Returns:
            List of employee calculation results or None if not found/not requested
        """
        if latest:
            # Return None to trigger recalculation
            return None
        
        month_prefix = str(month).zfill(2)
        data_key = f"{month_prefix}_{year}_DATA"
        
        param = SystemParameter.query.filter_by(param_key=data_key).first()
        if param and param.param_value:
            try:
                return json.loads(param.param_value)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return None

    @staticmethod
    def save_calculated_data(month: int, year: int, data: List[Dict[str, Any]]) -> None:
        """Save calculated data to database
        
        Args:
            month: Month number (1-12)
            year: Year (e.g., 2026)
            data: List of employee calculation results
        """
        month_prefix = str(month).zfill(2)
        data_key = f"{month_prefix}_{year}_DATA"
        
        param = SystemParameter.query.filter_by(param_key=data_key).first()
        if param:
            param.param_value = json.dumps(data)
            param.description = f"Calculated data for {month_prefix}/{year}"
        else:
            param = SystemParameter(
                param_key=data_key,
                param_value=json.dumps(data),
                description=f"Calculated data for {month_prefix}/{year}"
            )
            db.session.add(param)
        db.session.commit()

    @staticmethod
    def add_params(params: List[Dict[str, Any]], month: int = None) -> Dict[str, Any]:
        """Add new formula parameters or formulas
        
        Args:
            params: List of param objects, each containing:
                - param_key: The parameter/formula key to add
                - param_value: The parameter/formula value
                - description: Optional description
                - param_type: Type of item to add - "param" or "formula" (default: "param")
            month: Month number (1-12). If provided, stores with month prefix.
            
        Returns:
            Dict with all formula params after adding
        """
        # Process each param in the array
        for param in params:
            param_key = param.get("param_key")
            param_value = param.get("param_value")
            description = param.get("description")
            
            # Create the system parameter with month prefix if provided
            FormulaDAO.set_param(param_key, param_value, month, description)
        
        # Return current params and formulas
        return {
            "parameters": FormulaDAO.get_all_params(month),
            "formulas": FormulaDAO.get_formulas(month)
        }
    
    @staticmethod
    def add_param(param_key: str, param_value: str, description: str = None, param_type: str = "param", month: int = None) -> Dict[str, Any]:
        """Add a new formula parameter or formula (legacy single param method)
        
        Creates a new system parameter row. For formulas (param_type="formula"), 
        keys ending with _FORMULA_STRING are auto-detected.
        
        Args:
            param_key: The parameter/formula key to add
            param_value: The parameter/formula value
            description: Optional description
            param_type: Type of item to add - "param" or "formula" (default: "param")
            month: Month number (1-12). If provided, stores with month prefix.
            
        Returns:
            Dict with all formula params after adding
        """
        # Convert single param to array format
        params = [{
            "param_key": param_key,
            "param_value": param_value,
            "description": description,
            "param_type": param_type
        }]
        return FormulaDAO.add_params(params, month)

