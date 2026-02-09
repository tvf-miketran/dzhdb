from app.models.employee import Employee
from app import db
from werkzeug.security import generate_password_hash

class EmployeeDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_employee_id(employee_id: str):
        return Employee.query.filter_by(employeeId=employee_id).first()
    
    @staticmethod
    def get_by_employee_email(email: str):
        return Employee.query.filter_by(email=email).first()
    
    @staticmethod
    def get_all():
        return Employee.query.all()
    
     # ---------- CREATE ----------
    @staticmethod
    def create(employee_id: str, email: str, password: str, **kwargs):
        try:
            employee = Employee(
                employeeId=employee_id,
                email=email,
                password=generate_password_hash(password),
                **kwargs  # allows optional fields
            )
            db.session.add(employee)
            db.session.commit()
            return employee
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def update_password(employee: Employee, new_password: str):
        employee.password = generate_password_hash(new_password)
        db.session.commit()