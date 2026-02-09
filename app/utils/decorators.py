from functools import wraps
from flask_jwt_extended import verify_jwt_in_request
from flask import jsonify
from app.utils.auth_helpers import get_current_user


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        user = get_current_user()
        if not user or user.role != "ADMIN":
            return jsonify({"msg": "Admin privilege required"}), 403

        return fn(*args, **kwargs)
    return wrapper