from flask import Flask
from flask_cors import CORS
import os
from config import Config
from extensions import db, jwt, migrate, celery

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Import models biar dikenali oleh Alembic
    

    # Setup celery
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )

    # Buat folder upload
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from routes.auth import auth_bp
    from routes.interview import interview_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')

    return app
