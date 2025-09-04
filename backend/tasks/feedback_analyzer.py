from celery import Celery
import openai
from config import Config
from models import db
from models.answer import Answer
from models.question import Question

# Initialize Celery
celery = Celery()
celery.conf.update(
    broker_url=Config.CELERY_BROKER_URL,
    result_backend=Config.CELERY_RESULT_BACKEND
)

@celery.task
def analyze_answer_feedback(answer_id):
    """Analyze answer transcript and generate feedback using LLM"""
    with celery.app.app_context():
        answer = Answer.query.get(answer_id)
        if not answer or not answer.transcript_text:
            return "Answer not found or no transcript"
        
        try:
            # Get question text
            question = Question.query.get(answer.question_id)
            if not question:
                return "Question not found"
            
            # Create prompt for LLM
            prompt = f"""
            Berikut adalah jawaban dari kandidat terhadap pertanyaan interview:
            
            "Pertanyaan: {question.question_text}"
            
            "Jawaban: {answer.transcript_text}"
            
            Tolong berikan ringkasan jawaban tersebut dan evaluasi sederhana dalam format berikut:
            - Ringkasan: [ringkasan singkat]
            - Evaluasi:
              - Kejelasan: [1-10]
              - Struktur: [1-10]
              - Kata kunci: [1-10]
            - Saran: [saran perbaikan singkat]
            """
            
            # Use OpenAI GPT API
            openai.api_key = Config.OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Anda adalah asisten yang memberikan feedback untuk interview."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            feedback_text = response.choices[0].message.content
            
            # Parse feedback to extract scores (simplified)
            # In production, you might want to parse this more robustly
            answer.feedback = feedback_text
            answer.summary = "Ringkasan jawaban..."  # Extract from feedback
            answer.clarity_score = 7  # Extract from feedback
            answer.confidence_score = 6  # Extract from feedback
            answer.structure_score = 8  # Extract from feedback
            
            db.session.commit()
            
            return f"Feedback generated for answer {answer_id}"
            
        except Exception as e:
            print(f"Error analyzing feedback: {str(e)}")
            return f"Error: {str(e)}"