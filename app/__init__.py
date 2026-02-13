from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy import text

from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app import models

    CORS(
        app,
        resources={r"/api/*": {
            # "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
            "origins": "*", 
            "allow_headers": ["Content-Type", "Authorization", "ngrok-skip-browser-warning"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "credentials": False,
        }}
    )

    from app.exceptions.handlers import register_error_handlers
    register_error_handlers(app)

    # from app.routes import init_api
    # init_api(app)

    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
            print("✅ Kết nối database thành công!")
        except Exception as e:
            print("❌ Kết nối database thất bại!")
            print(f"🔥 Lỗi: {str(e)}")

    return app