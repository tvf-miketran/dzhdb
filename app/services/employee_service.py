from typing import Optional, List, Tuple, Dict, Any
from app.dao.employee_dao import EmployeeDAO
from app.models.employee import Employee


class EmployeeService:
    
    @staticmethod
    def get_all() -> List[Employee]:
        """Get all employees"""
        return EmployeeDAO.get_all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        status: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get filtered and sorted employees with pagination"""
        
        # Validate sort_by field
        valid_sort_fields = ["created_at", "updated_at", "vn_full_name", "en_full_name", "email", "employeeId", "status"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"
        
        pagination = EmployeeDAO.get_all_filtered_sorted(
            page=page,
            per_page=per_page,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "items": [EmployeeService._to_dict(emp) for emp in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
            "filters": {
                "status": status,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    @staticmethod
    def get_by_id(id: str) -> Optional[Employee]:
        """Get employee by UUID"""
        return EmployeeDAO.get_by_id(id)
    
    @staticmethod
    def get_by_employee_id(employee_id: str) -> Optional[Employee]:
        """Get employee by employeeId"""
        return EmployeeDAO.get_by_employee_id(employee_id)
    
    @staticmethod
    def create(
        employee_id: str,
        email: str,
        password: str,
        vn_full_name: str,
        en_full_name: str,
        description: str,
        authorize_role: str = "MEMBER",
        status: bool = True
    ) -> Tuple[Optional[Employee], Optional[List[str]]]:
        """Create new employee with validation"""
        errors = []
        
    # Check if employeeId already exists (skip check if it's "N/A")
        if employee_id != "N/A":
            if EmployeeDAO.get_by_employee_id(employee_id):
                errors.append(f"Employee ID '{employee_id}' already exists")
        
        # Check if email already exists
        if EmployeeDAO.get_by_employee_email(email):
            errors.append(f"Email '{email}' already exists")
        
        if errors:
            return None, errors
        
        try:
            employee = EmployeeDAO.create(
                employee_id=employee_id,
                email=email,
                password=password,
                vn_full_name=vn_full_name,
                en_full_name=en_full_name,
                description=description,
                authorize_role=authorize_role,
                status=status
            )
            return employee, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def update(
        id: str,
        vn_full_name: str = None,
        en_full_name: str = None,
        email: str = None,
        employee_id: str = None,
        description: str = None,
        authorize_role: str = None,
        status: bool = None
    ) -> Tuple[Optional[Employee], Optional[List[str]]]:
        """Update employee"""
        employee = EmployeeDAO.get_by_id(id)
        
        if not employee:
            return None, ["Employee not found"]
        
        errors = []
        
        # Check if new employeeId already exists (for different employee)
        if employee_id and employee_id != employee.employeeId:
            existing = EmployeeDAO.get_by_employee_id(employee_id)
            if existing:
                errors.append(f"Employee ID '{employee_id}' already exists")
        
        # Check if new email already exists (for different employee)
        if email and email != employee.email:
            existing = EmployeeDAO.get_by_employee_email(email)
            if existing:
                errors.append(f"Email '{email}' already exists")
        
        if errors:
            return None, errors
        
        try:
            updated = EmployeeDAO.update(
                id=id,
                vn_full_name=vn_full_name,
                en_full_name=en_full_name,
                email=email,
                employee_id=employee_id,
                description=description,
                authorize_role=authorize_role,
                status=status
            )
            return updated, None
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def toggle_status(id: str) -> Tuple[Optional[Employee], Optional[str]]:
        """Toggle employee status (active <-> inactive)"""
        employee = EmployeeDAO.get_by_id(id)
        
        if not employee:
            return None, "Employee not found"
        
        try:
            updated = EmployeeDAO.toggle_status(employee)
            return updated, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def set_status(id: str, status: bool) -> Tuple[Optional[Employee], Optional[str]]:
        """Set employee status explicitly"""
        employee = EmployeeDAO.get_by_id(id)
        
        if not employee:
            return None, "Employee not found"
        
        try:
            updated = EmployeeDAO.set_status(employee, status)
            return updated, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def _to_dict(employee: Employee) -> Dict[str, Any]:
        """Convert employee to dictionary"""
        return {
            "id": str(employee.id),
            "employeeId": employee.employeeId,
            "email": employee.email,
            "vnFullName": employee.vn_full_name,
            "enFullName": employee.en_full_name,
            "description": employee.description,
            "authorizeRole": employee.authorize_role,
            "status": employee.status,
            "createdAt": employee.created_at.isoformat() if employee.created_at else None,
            "updatedAt": employee.updated_at.isoformat() if employee.updated_at else None
        }