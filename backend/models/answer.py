from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from extensions import db


class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    audio_file_path = db.Column(db.String(255))
    transcript_text = db.Column(db.Text)
    summary = db.Column(db.Text)
    feedback = db.Column(db.Text)
    clarity_score = db.Column(db.Integer)  # 1-10
    confidence_score = db.Column(db.Integer)  # 1-10
    structure_score = db.Column(db.Integer)  # 1-10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'audio_file_path': self.audio_file_path,
            'transcript_text': self.transcript_text,
            'summary': self.summary,
            'feedback': self.feedback,
            'clarity_score': self.clarity_score,
            'confidence_score': self.confidence_score,
            'structure_score': self.structure_score,
            'created_at': self.created_at.isoformat()
        }