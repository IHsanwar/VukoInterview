from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
import threading

from config import Config
from utils.rabbitmq_handler import rabbitmq_handler
from tasks.stt_processor import start_stt_worker
from tasks.feedback_analyzer import start_feedback_worker
from extensions import db, jwt, migrate
from routes.detect_face import face_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.interview import interview_bp
    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')
    
    app.register_blueprint(face_bp, url_prefix='/api/face')
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        app.run(debug=True, threaded=True)
