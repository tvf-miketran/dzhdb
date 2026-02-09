from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.routes.auth import auth_bp

api_bp.register_blueprint(auth_bp, url_prefix="/auth")