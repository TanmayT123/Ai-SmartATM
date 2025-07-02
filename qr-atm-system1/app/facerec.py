from flask import Blueprint, request, render_template, jsonify
from app.db import get_db
import base64
import cv2
import numpy as np
import face_recognition

facerec_bp = Blueprint('facerec_bp', __name__)

# Route to open the match face page (Webcam preview + verify button)
@facerec_bp.route('/match_face')
def match_face_page():
    return render_template('match_face.html')


# ✅ Updated function: Now includes proper face distance comparison
def verify_face_from_base64(phone, image_base64):
    db = get_db()
    record = db.face_data.find_one({"phone": phone})
    if not record:
        return False, "❌ Face not registered. Please register first."

    try:
        # Decode image from base64
        input_bytes = base64.b64decode(image_base64.split(',')[1])
        input_np = np.frombuffer(input_bytes, np.uint8)
        input_img = cv2.imdecode(input_np, cv2.IMREAD_COLOR)

        # Convert image to RGB
        rgb_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)

        # Get face encoding from input image
        input_encodings = face_recognition.face_encodings(rgb_img)
        if not input_encodings:
            return False, "❌ No face detected in image."

        input_encoding = input_encodings[0]
        stored_encoding = np.array(record['encoding'])

        # Compare faces using distance
        distance = face_recognition.face_distance([stored_encoding], input_encoding)[0]
        print(f"ℹ️ Face distance: {distance:.4f}")

        # Define match threshold
        threshold = 0.5

        if distance <= threshold:
            return True, "✅ Face verified!"
        else:
            return False, "❌ Face does not match."

    except Exception as e:
        return False, f"❌ Error during verification: {str(e)}"


# API Route to verify the face from frontend
@facerec_bp.route('/verify-face', methods=['POST'])
def verify_face():
    from bson.objectid import ObjectId
    from flask import session

    data = request.get_json()
    image_data = data.get("image")

    if 'user_id' not in session or not image_data:
        return jsonify({"success": False, "message": "Not authenticated or image missing"})

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user:
        return jsonify({"success": False, "message": "User not found in session"})

    phone = user['phone']

    # Reuse verification logic
    success, message = verify_face_from_base64(phone, image_data)
    return jsonify({"success": success, "message": message})
