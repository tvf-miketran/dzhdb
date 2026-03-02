from sqlalchemy import Tuple, asc, desc
from sqlalchemy.orm import joinedload
from app.models.employee import Employee
from app import db
from werkzeug.security import generate_password_hash
from typing import Optional, List
from app.models.project_emp import ProjectMember


def _with_projects():
    """Reusable joinedload options for project_members → project + role"""
    return [
        joinedload(Employee.project_members).joinedload(ProjectMember.project),
        joinedload(Employee.project_members).joinedload(ProjectMember.role),
    ]


class EmployeeDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[Employee]:
        """Get employee by UUID"""
        return Employee.query.options(*_with_projects()).filter_by(id=id).first()

    @staticmethod
    def get_by_employee_id(employee_id: str) -> Optional[Employee]:
        return Employee.query.options(*_with_projects()).filter_by(employeeId=employee_id).first()
    
    @staticmethod
    def get_by_employee_email(email: str) -> Optional[Employee]:
        return Employee.query.options(*_with_projects()).filter_by(email=email).first()
    
    @staticmethod
    def get_all() -> List[Employee]:
        return Employee.query.options(*_with_projects()).all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        status: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """Get filtered and sorted employees with pagination"""
        query = Employee.query.options(*_with_projects())

        if status is not None:
            query = query.filter(Employee.status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Employee.vn_full_name.ilike(search_pattern),
                    Employee.en_full_name.ilike(search_pattern),
                    Employee.email.ilike(search_pattern),
                    Employee.employeeId.ilike(search_pattern)
                )
            )

        # Apply sorting
        sort_column = getattr(Employee, sort_by, Employee.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        return query.paginate(page=page, per_page=per_page, error_out=False)

    # ---------- CREATE ----------
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
    ) -> Employee:
        try:
            employee = Employee(
                employeeId=employee_id,
                email=email,
                password=generate_password_hash(password),
                vn_full_name=vn_full_name,
                en_full_name=en_full_name,
                description=description,
                authorize_role=authorize_role,
                status=status
            )
            db.session.add(employee)
            db.session.commit()
            return employee
        except Exception:
            db.session.rollback()
            raise

    # ---------- UPDATE ----------
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
    ) -> Employee:
        """Update employee"""
        try:
            employee = EmployeeDAO.get_by_id(id)
            
            if not employee:
                raise ValueError("Employee not found")
            
            # Validate employeeId uniqueness (if changing)
            if employee_id and employee_id != employee.employeeId:
                existing = EmployeeDAO.get_by_employee_id(employee_id)
                if existing and existing.id != employee.id:
                    raise ValueError(f"Employee ID '{employee_id}' already exists")
            
            # Validate email uniqueness (if changing)
            if email and email != employee.email:
                existing = EmployeeDAO.get_by_employee_email(email)
                if existing and existing.id != employee.id:
                    raise ValueError(f"Email '{email}' already exists")
            
            # Update fields
            if vn_full_name is not None:
                employee.vn_full_name = vn_full_name
            
            if en_full_name is not None:
                employee.en_full_name = en_full_name
            
            if email is not None:
                employee.email = email
            
            if employee_id is not None:
                employee.employeeId = employee_id
            
            if description is not None:
                employee.description = description
            
            if authorize_role is not None:
                employee.authorize_role = authorize_role
            
            if status is not None:
                employee.status = status
            
            db.session.commit()
            return employee
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_password(employee: Employee, new_password: str):
        try:
            employee.password = generate_password_hash(new_password)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    # ---------- STATUS MANAGEMENT ----------
    @staticmethod
    def toggle_status(employee: Employee) -> Employee:
        """Toggle employee status (active/inactive)"""
        try:
            employee.status = not employee.status
            db.session.commit()
            return employee
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_status(employee: Employee, status: bool) -> Employee:
        """Set employee status explicitly"""
        try:
            employee.status = status
            db.session.commit()
            return employee
        except Exception:
            db.session.rollback()
            raise