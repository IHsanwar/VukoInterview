from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
import json
import time

from extensions import db
from models.users import User
from models.role import Role
from models.question import Question
from models.session import InterviewSession
from models.answer import Answer
from utils.rabbitmq_handler import rabbitmq_handler

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
    
    file = request.files.get('audio') or request.files.get('video')
    if not file:
        return jsonify({'message': 'No media file provided'}), 400
    
    session_id = request.form.get('session_id')
    question_id = request.form.get('question_id')
    
    if not session_id or not question_id:
        return jsonify({'message': 'Session ID and Question ID are required'}), 400
    
    # Verify session belongs to user
    session = InterviewSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'message': 'Invalid session'}), 400
    


    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    answer = Answer(
        session_id=session_id,
        question_id=question_id,
        audio_file_path=file_path
    )
    print (answer)
    db.session.add(answer)
    db.session.commit()
    print(f"SDB Succces")
    # Trigger STT processing via RabbitMQ
    try:
        message = {
            'answer_id': answer.id,
            'timestamp': int(time.time())
        }
        
        rabbitmq_handler.publish_message('stt_processing', message)
        print(f"STT processing triggered for answer {answer.id}")
        
    except Exception as e:
        print(f"Error triggering STT processing: {e}")
        return jsonify({'message': 'Failed to trigger processing'}), 500
    
    return jsonify({
        'answer_id': answer.id,
        'message': 'Audio uploaded successfully. Processing started.'
    }), 201


@interview_bp.route('/session-complete',methods =['DELETE'])
@jwt_required()
def complete_session():
    user_id = get_jwt_identity()
    data = request.get_json()
    session_id = data.get('session_id')
    delete_session = InterviewSession.query.filter_by(id=session_id,user_id=user_id).first()
    if not delete_session:
        return jsonify({'message': 'Session not found'}), 404

    db.session.delete(delete_session)
    db.session.commit()

    return jsonify({'message': 'Session completed successfully'}), 200
