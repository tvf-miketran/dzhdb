from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

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
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "credentials": False,
        }}
    )

    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    return app