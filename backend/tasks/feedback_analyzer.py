import openai
import json
import time
import threading
from config import Config
from extensions import db
from models.answer import Answer
from models.question import Question
import pika

def analyze_answer_feedback(answer_id):
    """Analyze answer transcript and generate feedback using LLM"""
    try:
        print(f"🔍 Starting feedback analysis for answer {answer_id}")
        
        # Import app inside function to avoid circular imports
        from app import create_app
        app = create_app()
        
        with app.app_context():
            answer = Answer.query.get(answer_id)
            if not answer or not answer.transcript_text:
                print(f"❌ Answer {answer_id} not found or no transcript")
                return False
            
            # Get question text
            question = Question.query.get(answer.question_id)
            if not question:
                print(f"❌ Question for answer {answer_id} not found")
                return False
            
            print(f"📝 Analyzing feedback for answer {answer_id}")
            print(f"❓ Question: {question.question_text}")
            print(f"💬 Transcript: {answer.transcript_text[:100]}...")
            
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
            
            print(f"🔄 Sending to OpenAI GPT API...")
            
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
            answer.feedback = feedback_text
            answer.summary = "Ringkasan jawaban..."  # Extract from feedback
            answer.clarity_score = 7  # Extract from feedback
            answer.confidence_score = 6  # Extract from feedback
            answer.structure_score = 8  # Extract from feedback
            
            # Try to commit and handle errors
            try:
                db.session.commit()
                print(f"✅ Feedback saved to database for answer {answer_id}")
                return True
                
            except Exception as e:
                print(f"❌ Error saving feedback to database: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                return False
            
    except Exception as e:
        print(f"❌ Error analyzing feedback for answer {answer_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    

def start_feedback_worker():
    """Start feedback analysis worker"""
    def worker():
        try:
            print("🔄 Initializing Feedback Worker...")
            
            from config import Config
            credentials = pika.PlainCredentials(
                Config.RABBITMQ_USER, 
                Config.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            print(f"🔗 Connecting to RabbitMQ: {Config.RABBITMQ_HOST}:{Config.RABBITMQ_PORT}")
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            channel.queue_declare(queue='feedback_analysis', durable=True)
            print("✅ Feedback queue declared")
            
            def callback(ch, method, properties, body):
                try:
                    print(f"📥 Received feedback message: {body}")
                    message = json.loads(body)
                    answer_id = message.get('answer_id')
                    print(message)
                    if answer_id:
                        print(f"⚙️ Processing feedback for answer {answer_id}")
                        success = analyze_answer_feedback(answer_id)
                        
                        if success:
                            print(f"✅ Feedback processing completed for answer {answer_id}")
                        else:
                            print(f"❌ Feedback processing failed for answer {answer_id}")
                    
                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    print(f"✅ Feedback message acknowledged")
                    
                except Exception as e:
                    print(f"❌ Error processing feedback message: {e}")
                    import traceback
                    traceback.print_exc()
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='feedback_analysis', on_message_callback=callback)
            
            print("🚀 Feedback Worker started. Waiting for messages...")
            channel.start_consuming()
            
        except Exception as e:
            print(f"💥 Feedback Worker error: {e}")
            import traceback
            traceback.print_exc()
    
    # Start worker in separate thread
    print("🧵 Starting Feedback worker thread...")
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    print("✅ Feedback worker thread started")
    return worker_thread