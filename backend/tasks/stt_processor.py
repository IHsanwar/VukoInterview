from celery import Celery
import openai
import os
from config import Config
from models import db
from models.answer import Answer

# Initialize Celery
celery = Celery()
celery.conf.update(
    broker_url=Config.CELERY_BROKER_URL,
    result_backend=Config.CELERY_RESULT_BACKEND
)

@celery.task
def process_audio_to_text(answer_id):
    """Process audio file to text using OpenAI Whisper"""
    with celery.app.app_context():
        answer = Answer.query.get(answer_id)
        if not answer or not answer.audio_file_path:
            return "Answer not found or no audio file"
        
        try:
            openai.api_key = Config.OPENAI_API_KEY
            
            with open(answer.audio_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)

            answer.transcript_text = transcript['text']
            db.session.commit()
            
            from tasks.feedback_analyzer import analyze_answer_feedback
            analyze_answer_feedback.delay(answer_id)
            
            return f"Transcript processed for answer {answer_id}"
            
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            return f"Error: {str(e)}"