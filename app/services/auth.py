from flask_jwt_extended import create_access_token
from app.dao.employee_dao import EmployeeDAO
from app.utils.auth_helpers import verify_password


class AuthService:

    @staticmethod
    def login(email: str, password: str):
        employee = EmployeeDAO.get_by_employee_email(email)

        if not employee or not verify_password(password, employee.password):
            return None

        return create_access_token(identity=employee.employeeId)

    @staticmethod
    def get_current_employee(employee_id: str):
        return EmployeeDAO.get_by_employee_id(employee_id)

    @staticmethod
    def reset_password(employee_id: str, old_password: str, new_password: str) -> bool:
        employee = EmployeeDAO.get_by_employee_id(employee_id)

        if not employee:
            return False

        if not verify_password(old_password, employee.password):
            return False

        EmployeeDAO.update_password(employee, new_password)
        return True