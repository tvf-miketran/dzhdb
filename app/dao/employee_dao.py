from app.models.employee import Employee
from app import db
from werkzeug.security import generate_password_hash

class EmployeeDAO:

    @staticmethod
    def get_by_employee_id(employee_id: str):
        return Employee.query.filter_by(employeeId=employee_id).first()
    
    @staticmethod
    def update_password(employee: Employee, new_password: str):
        employee.password = generate_password_hash(new_password)
        db.session.commit()