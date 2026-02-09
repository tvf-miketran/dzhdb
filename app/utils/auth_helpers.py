from flask_jwt_extended import get_jwt_identity
from app.models.employee import Employee
from werkzeug.security import check_password_hash


def get_current_user():
    employeeId = get_jwt_identity()
    if not employeeId:
        return None

    return Employee.query.filter_by(employeeId=employeeId).first()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)