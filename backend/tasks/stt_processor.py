import openai
import json
import os
import threading
import time
from config import Config
from extensions import db
from models.answer import Answer
from utils.rabbitmq_handler import rabbitmq_handler
import pika

def process_audio_to_text(answer_id):
    """Process audio file to text using OpenAI Whisper"""
    try:
        print(f"🔍 Starting STT processing for answer {answer_id}")
        
        # Import app inside function to avoid circular imports
        from app import create_app
        app = create_app()
        
        with app.app_context():
            print(f"🔎 Querying Answer with id: {answer_id}")
            answer = Answer.query.get(answer_id)
            print(f"🔎 Query result: {answer}")
            if not answer or not answer.audio_file_path:
                print(f"❌ Answer {answer_id} not found or no audio file")
                return False
            
            print(f"📂 Audio file path: {answer.audio_file_path}")
            
            # Check if file exists
            if not os.path.exists(answer.audio_file_path):
                print(f"❌ Audio file not found: {answer.audio_file_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(answer.audio_file_path)
            print(f"🔊 Audio file size: {file_size} bytes")
            
            if file_size == 0:
                print(f"❌ Audio file is empty")
                return False
            
            # Use OpenAI Whisper API
            openai.api_key = Config.OPENAI_API_KEY
            
            print(f"🔄 Sending to OpenAI Whisper API...")
            
            with open(answer.audio_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
            
            print(f"📝 OpenAI Whisper API response: {transcript}")
            # Update answer with transcript
            answer.transcript_text = transcript['text']
            print(f"📝 Transcript: {answer.transcript_text[:100]}...")
            
            # Try to commit and handle errors
            try:
                print("💾 Committing transcript to database...")
                db.session.commit()
                print(f"✅ Transcript saved to database for answer {answer_id}")
                return True
                
            except Exception as e:
                print(f"❌ Error saving transcript to database: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                return False
            
            # Trigger feedback analysis
            trigger_feedback_analysis(answer_id)
            return True
            
    except Exception as e:
        print(f"❌ Error processing audio for answer {answer_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def trigger_feedback_analysis(answer_id):
    """Trigger feedback analysis via RabbitMQ"""
    try:
        print(f"🔔 Triggering feedback analysis for answer {answer_id}")
        message = {
            'answer_id': answer_id,
            'timestamp': int(time.time())
        }
        
        rabbitmq_handler.publish_message('feedback_analysis', message)
        print(f"🚀 Feedback analysis triggered for answer {answer_id}")
        
    except Exception as e:
        print(f"❌ Error triggering feedback analysis: {e}")

def start_stt_worker():
    """Start STT processing worker"""
    def worker():
        try:
            print("🔄 Initializing STT Worker...")
            
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
            
            channel.queue_declare(queue='stt_processing', durable=True)
            print("✅ STT queue declared")
            
            def callback(ch, method, properties, body):
                try:
                    print(f"📥 Received message: {body}")
                    message = json.loads(body)
                    print(f"📦 Decoded message: {message}")
                    answer_id = message.get('answer_id')
                    
                    if answer_id:
                        print(f"⚙️ Processing STT for answer {answer_id}")
                        success = process_audio_to_text(answer_id)
                        
                        if success:
                            print(f"✅ STT processing completed for answer {answer_id}")
                        else:
                            print(f"❌ STT processing failed for answer {answer_id}")
                    
                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    print(f"✅ Message acknowledged")
                    
                except Exception as e:
                    print(f"❌ Error processing STT message: {e}")
                    import traceback
                    traceback.print_exc()
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='stt_processing', on_message_callback=callback)
            
            print("🚀 STT Worker started. Waiting for messages...")
            channel.start_consuming()
            
        except Exception as e:
            print(f"💥 STT Worker error: {e}")
            import traceback
            traceback.print_exc()
    
    # Start worker in separate thread
    print("🧵 Starting STT worker thread...")
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    print("✅ STT worker thread started")
    return worker_thread