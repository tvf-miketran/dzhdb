# app/services/auth_service.py
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash
from app.dao.employee_dao import EmployeeDAO
from app.utils.auth_helpers import verify_password
from app import db


class AuthService:

    @staticmethod
    def login(employee_id: str, password: str):
        employee = EmployeeDAO.get_by_employee_id(employee_id)

        if not employee or not verify_password(password, employee.password):
            return None

        token = create_access_token(identity=employee.employeeId)
        return token

    @staticmethod
    def get_current_employee(employee_id: str):
        return EmployeeDAO.get_by_employee_id(employee_id)