from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.routes.auth_router import auth_bp
from app.routes.employee_router import employee_bp
from app.routes.project_router import project_bp
from app.routes.bank_router import bank_bp
from app.routes.logwork_router import logwork_bp
from app.routes.role_router import role_bp

api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(employee_bp, url_prefix="/employees")
api_bp.register_blueprint(project_bp, url_prefix="/projects")
api_bp.register_blueprint(bank_bp, url_prefix="/banks")
api_bp.register_blueprint(logwork_bp, url_prefix="/logworks")
api_bp.register_blueprint(role_bp, url_prefix="/roles")