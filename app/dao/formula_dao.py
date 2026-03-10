from typing import Optional, Dict, Any, List
import json
from app.models.systemparam import SystemParameter
from app import db


class FormulaDAO:
    """DAO for managing formula system parameters in the database"""

    # Key for storing param keys in system_parameters
    PARAM_KEYS_KEY = "FORMULA_PARAM_KEYS"
    
    # Key for storing formula name keys in system_parameters
    FORMULA_NAME_KEYS_KEY = "FORMULA_NAME_KEYS"
    
    # Key for storing formula required params mapping
    FORMULA_REQUIRED_PARAMS_KEY = "FORMULA_REQUIRED_PARAMS"

    # Default formula name keys (for identifying formula types)
    DEFAULT_FORMULA_NAME_KEYS = [
        "TICKET_FORMULA_STRING",
        "LOGWORK_FORMULA_STRING",
        "MEMBER_CONTR_POINT_FORMULA_STRING",
        "BILLABLE_POINT_FORMULA_STRING"
    ]

    # Default param keys (fallback if not in database)
    DEFAULT_PARAM_KEYS = [
        "TASK_WEIGHT",
        "BUG_WEIGHT",
        "DEV_ROLE_WEIGHT",
        "BA_ROLE_WEIGHT",
        "IQA_ROLE_WEIGHT",
        "EQA_ROLE_WEIGHT",
        "REVIEWER_ROLE_WEIGHT",
        "STANDARD_DEV",
        "STANDARD_BA",
        "STANDARD_QA",
        "STANDARD_REVIEWER",
        "STANDARD_LOGWORK",
        "BILLABLE_PARAM",
    ]

    @staticmethod
    def get_param_keys() -> List[str]:
        """Get formula parameter keys from database, or return defaults"""
        param = SystemParameter.query.filter_by(param_key=FormulaDAO.PARAM_KEYS_KEY).first()
        if param and param.param_value:
            try:
                return json.loads(param.param_value)
            except (json.JSONDecodeError, TypeError):
                pass
        return FormulaDAO.DEFAULT_PARAM_KEYS

    @staticmethod
    def set_param_keys(param_keys: List[str]) -> None:
        """Store formula parameter keys in database"""
        param = SystemParameter.query.filter_by(param_key=FormulaDAO.PARAM_KEYS_KEY).first()
        if param:
            param.param_value = json.dumps(param_keys)
            param.description = "Formula parameter keys"
        else:
            param = SystemParameter(
                param_key=FormulaDAO.PARAM_KEYS_KEY,
                param_value=json.dumps(param_keys),
                description="Formula parameter keys"
            )
            db.session.add(param)
        db.session.commit()
    
    @staticmethod
    def get_formula_name_keys() -> List[str]:
        """Get formula name keys from database, or return defaults"""
        param = SystemParameter.query.filter_by(param_key=FormulaDAO.FORMULA_NAME_KEYS_KEY).first()
        if param and param.param_value:
            try:
                return json.loads(param.param_value)
            except (json.JSONDecodeError, TypeError):
                pass
        return FormulaDAO.DEFAULT_FORMULA_NAME_KEYS

    @staticmethod
    def set_formula_name_keys(formula_name_keys: List[str]) -> None:
        """Store formula name keys in database"""
        param = SystemParameter.query.filter_by(param_key=FormulaDAO.FORMULA_NAME_KEYS_KEY).first()
        if param:
            param.param_value = json.dumps(formula_name_keys)
            param.description = "Formula name keys"
        else:
            param = SystemParameter(
                param_key=FormulaDAO.FORMULA_NAME_KEYS_KEY,
                param_value=json.dumps(formula_name_keys),
                description="Formula name keys"
            )
            db.session.add(param)
        db.session.commit()
    
    @staticmethod
    def get_formula_required_params(formula_key: str = None) -> Dict[str, List[str]]:
        """Get formula required params mapping from database
        
        Args:
            formula_key: If provided, returns only that formula's required params
            
        Returns:
            Dict mapping formula_key -> list of required param keys
        """
        param = SystemParameter.query.filter_by(param_key=FormulaDAO.FORMULA_REQUIRED_PARAMS_KEY).first()
        if param and param.param_value:
            try:
                mapping = json.loads(param.param_value)
                if formula_key:
                    return mapping.get(formula_key, [])
                return mapping
            except (json.JSONDecodeError, TypeError):
                pass
        return {} if formula_key is None else []
    
    @staticmethod
    def set_formula_required_params(mapping: Dict[str, List[str]]) -> None:
        """Store formula required params mapping in database
        
        Args:
            mapping: Dict mapping formula_key -> list of required param keys
        """
        param = SystemParameter.query.filter_by(param_key=FormulaDAO.FORMULA_REQUIRED_PARAMS_KEY).first()
        if param:
            param.param_value = json.dumps(mapping)
            param.description = "Formula required parameters mapping"
        else:
            param = SystemParameter(
                param_key=FormulaDAO.FORMULA_REQUIRED_PARAMS_KEY,
                param_value=json.dumps(mapping),
                description="Formula required parameters mapping"
            )
            db.session.add(param)
        db.session.commit()
    
    @staticmethod
    def add_formula_required_param(formula_key: str, required_param: str) -> None:
        """Add a required param to a formula
        
        Args:
            formula_key: The formula key
            required_param: The required parameter key
        """
        mapping = FormulaDAO.get_formula_required_params()
        if formula_key not in mapping:
            mapping[formula_key] = []
        if required_param not in mapping[formula_key]:
            mapping[formula_key].append(required_param)
        FormulaDAO.set_formula_required_params(mapping)
    
    @staticmethod
    def is_ticket_formula(formula_key: str) -> bool:
        """Check if formula key is for ticket"""
        return formula_key.startswith("TICKET_")
    
    @staticmethod
    def is_logwork_formula(formula_key: str) -> bool:
        """Check if formula key is for logwork"""
        return formula_key.startswith("LOGWORK_")

    @staticmethod
    def get_param(param_key: str) -> Optional[str]:
        """Get system parameter value by key"""
        param = SystemParameter.query.filter_by(param_key=param_key).first()
        return param.param_value if param else None

    @staticmethod
    def set_param(param_key: str, param_value: str, description: str = None) -> SystemParameter:
        """Set system parameter value"""
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
    def get_all_params() -> Dict[str, Optional[str]]:
        """Get all formula parameters"""
        param_keys = FormulaDAO.get_param_keys()
        params = {}
        for key in param_keys:
            params[key] = FormulaDAO.get_param(key)
        return params

    @staticmethod
    def add_param(param_key: str, param_value: str, description: str = None, param_type: str = "param", required_params: List[str] = None) -> Dict[str, Any]:
        """Add a new formula parameter or formula
        
        Creates a new system parameter row and adds the key to either FORMULA_PARAM_KEYS
        (for parameters) or FORMULA_NAME_KEYS (for formulas). If adding a formula with
        required_params, those parameters will be automatically added as well.
        
        Args:
            param_key: The parameter/formula key to add
            param_value: The parameter/formula value
            description: Optional description
            param_type: Type of item to add - "param" or "formula" (default: "param")
            required_params: List of parameter keys this formula requires (only for type="formula")
            
        Returns:
            Dict with all formula params after adding
        """
        # Create the system parameter
        FormulaDAO.set_param(param_key, param_value, description)
        
        # Get current param keys
        param_keys = FormulaDAO.get_param_keys()
        
        if param_type == "formula":
            # Add to FORMULA_NAME_KEYS if not exists
            formula_name_keys = FormulaDAO.get_formula_name_keys()
            if param_key not in formula_name_keys:
                formula_name_keys.append(param_key)
                FormulaDAO.set_formula_name_keys(formula_name_keys)
            
            # Auto-add required parameters if provided
            if required_params:
                # Store the required params mapping
                for req_param in required_params:
                    if req_param not in param_keys:
                        param_keys.append(req_param)
                        # Set default value for required param
                        FormulaDAO.set_param(req_param, "1", f"Required for {param_key}")
                FormulaDAO.set_param_keys(param_keys)
                # Also store the mapping for reference
                FormulaDAO.add_formula_required_param(param_key, required_params[0])
                # Update with full list
                mapping = FormulaDAO.get_formula_required_params()
                mapping[param_key] = required_params
                FormulaDAO.set_formula_required_params(mapping)
        else:
            # Add to FORMULA_PARAM_KEYS if not exists (default behavior)
            if param_key not in param_keys:
                param_keys.append(param_key)
                FormulaDAO.set_param_keys(param_keys)
        
        return FormulaDAO.get_all_params()

