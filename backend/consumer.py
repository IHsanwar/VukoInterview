import pika
import json
import time
import os
import threading
import traceback
import whisper
from config import Config
from extensions import db
from models.answer import Answer
from models.question import Question
import dotenv

import openai
from app import create_app
dotenv.load_dotenv()
def process_audio_to_text(answer_id):
    """Process audio file to text using local Whisper (optionally polish with GPT)"""
    try:
        print(f"🔍 Starting STT processing for answer {answer_id}")
        app = create_app()
        with app.app_context():
            print(f"🔎 Querying Answer with id: {answer_id}")
            answer = Answer.query.get(answer_id)
            print(f"🔎 Query result: {answer}")
            if not answer or not answer.audio_file_path:
                print(f"❌ Answer {answer_id} not found or no audio file")
                return False

            print(f"📂 Audio file path: {answer.audio_file_path}")
            if not os.path.exists(answer.audio_file_path):
                print(f"❌ Audio file not found: {answer.audio_file_path}")
                return False

            file_size = os.path.getsize(answer.audio_file_path)
            print(f"🔊 Audio file size: {file_size} bytes")
            if file_size == 0:
                print(f"❌ Audio file is empty")
                return False

            print("🔄 Loading local Whisper model...")
            model = whisper.load_model("base")  

            print("🔄 Running transcription locally...")
            result = model.transcribe(answer.audio_file_path, fp16=False, language='id',temperature=0)
            transcript_text = result["text"]

            print(f"📝 Local Whisper transcript: {transcript_text[:100]}...")
            answer.transcript_text = transcript_text

            try:
                if Config.OPENAI_API_KEY:  
                    openai.api_key = Config.OPENAI_API_KEY
                    print("✨ Polishing transcript with GPT...")
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Anda adalah asisten yang merapikan"
                            " hasil transkrip audio tanpa mengubah makna atau materi yang dibahas, "
                            "pastikan hanya merapikan kata yang berantakan."},

                            {"role": "user", "content": transcript_text}
                        ],
                        max_tokens=1000,
                        temperature=0.2
                    )
                    polished_text = response.choices[0].message.content.strip()
                    print(f"📝 Polished transcript: {polished_text[:100]}...")
                    answer.transcript_text = polished_text
            except Exception as e:
                print(f"⚠️ Skipping GPT polish due to error: {e}")

            # === STEP 3: Simpan ke database ===
            try:
                print("💾 Committing transcript to database...")
                db.session.commit()
                print(f"✅ Transcript saved to database for answer {answer_id}")
                
                # 🔥 Trigger feedback analysis setelah STT selesai
                print(f"🚀 Triggering feedback analysis for answer {answer_id}")
                trigger_feedback_analysis(answer_id)
                
                return True
            except Exception as e:
                print(f"❌ Error saving transcript to database: {e}")
                traceback.print_exc()
                db.session.rollback()
                return False

    except Exception as e:
        print(f"❌ Error processing audio for answer {answer_id}: {str(e)}")
        traceback.print_exc()
        return False

def trigger_feedback_analysis(answer_id):
    """Trigger feedback analysis via RabbitMQ"""
    try:
        url = os.getenv('RABBITMQ_URL')
        parameters = pika.URLParameters(url)
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Pastikan queue ada
        channel.queue_declare(queue='feedback_analysis', durable=True)

        # Kirim pesan
        message = {
            'answer_id': answer_id,
            'timestamp': int(time.time())
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='feedback_analysis',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        
        print(f"✅ Feedback analysis triggered for answer {answer_id}")
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error triggering feedback analysis: {e}")
        traceback.print_exc()
        return False



def callback_stt(ch, method, properties, body):
    try:
        print(f"📥 [stt_processing] Received: {body}")
        data = json.loads(body)
        answer_id = data.get('answer_id')
        if answer_id:
            print(f"⚙️ Processing STT for answer {answer_id}")
            success = process_audio_to_text(answer_id)
            if success:
                print(f"✅ STT processing completed for answer {answer_id}")
            else:
                print(f"❌ STT processing failed for answer {answer_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"✅ [stt_processing] Message acknowledged")
    except Exception as e:
        print(f"❌ Error in STT callback: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def analyze_answer_feedback(answer_id):
    try:
        print(f"🔍 Starting feedback analysis for answer {answer_id}")
        app = create_app()
        with app.app_context():
            answer = Answer.query.get(answer_id)
            if not answer or not answer.transcript_text:
                print(f"❌ Answer {answer_id} not found or no transcript")
                return False

            question = Question.query.get(answer.question_id)
            if not question:
                print(f"❌ Question for answer {answer_id} not found")
                return False

            print(f"📝 Analyzing feedback for answer {answer_id}")
            print(f"❓ Question: {question.question_text}")
            print(f"💬 Transcript: {answer.transcript_text[:100]}...")

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
            print(f"💬 AI Feedback response: {feedback_text}")

            # 🔥 PENTING: Parsing feedback untuk ekstrak data
            answer.feedback = feedback_text
            
            # Parsing sederhana untuk ekstrak ringkasan dan skor
            lines = feedback_text.split('\n')
            for line in lines:
                if line.startswith('- Ringkasan:'):
                    answer.summary = line.replace('- Ringkasan:', '').strip()
                elif 'Kejelasan:' in line and 'Kejelasan: [1-10]' not in line:
                    # Coba ekstrak angka dari line seperti "Kejelasan: 8"
                    import re
                    clarity_match = re.search(r'Kejelasan:\s*(\d+)', line)
                    if clarity_match:
                        answer.clarity_score = int(clarity_match.group(1))
                elif 'Struktur:' in line and 'Struktur: [1-10]' not in line:
                    import re
                    structure_match = re.search(r'Struktur:\s*(\d+)', line)
                    if structure_match:
                        answer.structure_score = int(structure_match.group(1))
                elif 'Kata kunci:' in line and 'Kata kunci: [1-10]' not in line:
                    import re
                    confidence_match = re.search(r'Kata kunci:\s*(\d+)', line)
                    if confidence_match:
                        answer.confidence_score = int(confidence_match.group(1))

            # Jika parsing gagal, gunakan nilai default
            if not answer.summary:
                answer.summary = "Ringkasan jawaban..."
            if not answer.clarity_score:
                answer.clarity_score = 7
            if not answer.structure_score:
                answer.structure_score = 6
            if not answer.confidence_score:
                answer.confidence_score = 8

            try:
                db.session.commit()
                print(f"✅ Feedback saved to database for answer {answer_id}")
                print(f"📊 Summary: {answer.summary}")
                print(f"📊 Clarity Score: {answer.clarity_score}")
                print(f"📊 Structure Score: {answer.structure_score}")
                print(f"📊 Confidence Score: {answer.confidence_score}")
                return True
            except Exception as e:
                print(f"❌ Error saving feedback to database: {e}")
                traceback.print_exc()
                db.session.rollback()
                return False
    except Exception as e:
        print(f"❌ Error analyzing feedback for answer {answer_id}: {str(e)}")
        traceback.print_exc()
        return False

def callback_feedback(ch, method, properties, body):
    try:
        print(f"📥 [feedback_analysis] Received: {body}")
        data = json.loads(body)
        answer_id = data.get('answer_id')
        if answer_id:
            print(f"⚙️ Processing feedback for answer {answer_id}")
            success = analyze_answer_feedback(answer_id)
            if success:
                print(f"✅ Feedback processing completed for answer {answer_id}")
            else:
                print(f"❌ Feedback processing failed for answer {answer_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"✅ [feedback_analysis] Message acknowledged")
    except Exception as e:
        print(f"❌ Error in feedback callback: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    url = LOADOTENV_RABBITMQ_URL = os.getenv('RABBITMQ_URL')
    parameters = pika.URLParameters(url)
    parameters.heartbeat = 600
    parameters.blocked_connection_timeout = 300

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='stt_processing', durable=True)
    channel.queue_declare(queue='feedback_analysis', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='stt_processing', on_message_callback=callback_stt)
    channel.basic_consume(queue='feedback_analysis', on_message_callback=callback_feedback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Interrupted")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()