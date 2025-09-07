from flask import Blueprint, request, jsonify
import numpy as np
import cv2
import face_recognition
import base64

face_bp = Blueprint('face', __name__)

@face_bp.route('/detect-face', methods=['POST'])
def detect_face():
    try:
        data = request.json
        img_b64 = data.get('image')
        if not img_b64:
            return jsonify({'error': 'No image provided'}), 400

        img_bytes = base64.b64decode(img_b64.split(',')[-1])
        npimg = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)

        response = {
            'face_count': len(face_locations),
            'encodings': [enc.tolist() for enc in face_encodings]
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500