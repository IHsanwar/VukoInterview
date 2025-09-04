from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid

from models.users import db
from models.users import User
from models.role import Role
from models.question import Question
from models.session import InterviewSession
from models.answer import Answer

interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/roles', methods=['GET'])
def get_roles():
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles]), 200

@interview_bp.route('/start-session', methods=['POST'])
@jwt_required()
def start_session():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('role_id'):
        return jsonify({'message': 'Role ID is required'}), 400
    
    # Check if role exists
    role = Role.query.get(data['role_id'])
    if not role:
        return jsonify({'message': 'Invalid role ID'}), 400
    
    # Create new session
    session = InterviewSession(
        user_id=user_id,
        role_id=data['role_id']
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'session_id': session.id,
        'message': 'Session started successfully'
    }), 201

@interview_bp.route('/questions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_questions(session_id):
    user_id = get_jwt_identity()
    
    # Verify session belongs to user
    session = InterviewSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'message': 'Session not found'}), 404
    
    # Get questions for the role
    questions = Question.query.filter_by(role_id=session.role_id).all()
    
    return jsonify([q.to_dict() for q in questions]), 200

@interview_bp.route('/upload-answer', methods=['POST'])
@jwt_required()
def upload_answer():
    user_id = get_jwt_identity()
    
    # Check if file is present
    if 'audio' not in request.files:
        return jsonify({'message': 'No audio file provided'}), 400
    
    file = request.files['audio']
    session_id = request.form.get('session_id')
    question_id = request.form.get('question_id')
    
    if not session_id or not question_id:
        return jsonify({'message': 'Session ID and Question ID are required'}), 400
    
    # Verify session belongs to user
    session = InterviewSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'message': 'Invalid session'}), 400
    
    # Save file
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Create answer record
    answer = Answer(
        session_id=session_id,
        question_id=question_id,
        audio_file_path=file_path
    )
    
    db.session.add(answer)
    db.session.commit()
    
    # Trigger STT processing (Celery task)
    from tasks.stt_processor import process_audio_to_text
    process_audio_to_text.delay(answer.id)
    
    return jsonify({
        'answer_id': answer.id,
        'message': 'Audio uploaded successfully'
    }), 201