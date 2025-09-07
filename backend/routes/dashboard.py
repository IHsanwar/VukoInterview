# backend/routes/dashboard.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.answer import Answer
from models.session import InterviewSession
from models.question import Question
from extensions import db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/history", methods=["GET"])
def get_answers_history():

    # query join ke session + question
    answers = (
        db.session.query(Answer, Question)
        .join(InterviewSession, Answer.session_id == InterviewSession.id)
        .join(Question, Answer.question_id == Question.id)
        .order_by(Answer.created_at.desc())
        .all()
    )

    history = []
    for ans, q in answers:
        history.append({
            "answer_id": ans.id,
            "created_at": ans.created_at.isoformat(),
            "question_text": q.question_text if q else "",
            "clarity_score": ans.clarity_score,
            "structure_score": ans.structure_score,
            "confidence_score": ans.confidence_score,
            "transcript_text": ans.transcript_text,
        })

    return jsonify(history), 200

@dashboard_bp.route("/answers/<int:answer_id>", methods=["GET"])
def get_answer_details(answer_id):
    ans = Answer.query.get(answer_id)
    if not ans:
        return jsonify({"msg": "Answer not found"}), 404

    question = Question.query.get(ans.question_id)
    answer = Answer.query.get(answer_id)
    details = {
        "answer_id": ans.id,
        "created_at": ans.created_at.isoformat(),
        "question_text": question.question_text if question else "",
        "clarity_score": ans.clarity_score,
        "structure_score": ans.structure_score,
        "confidence_score": ans.confidence_score,
        "transcript_text": ans.transcript_text,
        "feedback": ans.feedback,
        "summary": ans.summary,}
    
    return jsonify(details), 200