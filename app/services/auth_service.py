from flask_jwt_extended import create_access_token
from app.dao.employee_dao import EmployeeDAO
from app.utils.auth_helpers import verify_password


class AuthService:

    @staticmethod
    def login(email: str, password: str):
        employee = EmployeeDAO.get_by_employee_email(email)

        if not employee or not verify_password(password, employee.password):
            error = "Invalid email or password"
            return None, error

        if employee.status is False:  # INACTIVE
            error = "Account is inactive. Please contact administrator."
            return None, error
        access_token = create_access_token(identity=employee.employeeId)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "UUID":employee.id,
                "employeeId": employee.employeeId,
                "email": employee.email,
                "en_full_name": employee.en_full_name,
                "vn_full_name": employee.vn_full_name,
                "authorize_role": employee.authorize_role,
                "status": employee.status,
                "description": employee.description,
            }
        } , None

    @staticmethod
    def get_current_employee(employee_id: str):
        return EmployeeDAO.get_by_employee_id(employee_id)

    @staticmethod
    def update_password(employee_id: str, old_password: str, new_password: str) -> bool:
        employee = EmployeeDAO.get_by_employee_id(employee_id)

        if not employee:
            return False

        if not verify_password(old_password, employee.password):
            return False

        EmployeeDAO.update_password(employee, new_password)
        return True

    @staticmethod
    def reset_password_to_email(employee_id: str) -> bool:
        """Reset password to match email (admin only operation)"""
        employee = EmployeeDAO.get_by_employee_id(employee_id)

        if not employee:
            return False

        EmployeeDAO.update_password(employee, employee.email)
        return True