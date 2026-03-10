from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.routes.auth_router import auth_bp
from app.routes.employee_router import employee_bp
from app.routes.project_router import project_bp
from app.routes.bank_router import bank_bp
from app.routes.logwork_router import logwork_bp
from app.routes.role_router import role_bp
from app.routes.ticket_router import ticket_bp
from app.routes.ticket_type_router import ticket_type_bp
from app.routes.ticket_status_router import ticket_status_bp
from app.routes.formula_router import formula_bp

api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(employee_bp, url_prefix="/employees")
api_bp.register_blueprint(project_bp, url_prefix="/projects")
api_bp.register_blueprint(bank_bp, url_prefix="/banks")
api_bp.register_blueprint(logwork_bp, url_prefix="/logworks")
api_bp.register_blueprint(role_bp, url_prefix="/roles")
api_bp.register_blueprint(ticket_bp, url_prefix="/tickets")
api_bp.register_blueprint(ticket_type_bp, url_prefix="/ticket-types")
api_bp.register_blueprint(ticket_status_bp, url_prefix="/ticket-statuses")
api_bp.register_blueprint(formula_bp, url_prefix="/formulas")
