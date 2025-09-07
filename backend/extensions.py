# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from celery import Celery

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
celery = Celery()
