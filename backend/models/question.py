from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from extensions import db


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    category = db.Column(db.String(50))  # technical, behavioral, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'question_text': self.question_text,
            'difficulty': self.difficulty,
            'category': self.category
        }