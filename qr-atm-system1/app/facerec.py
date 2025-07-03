from flask import Blueprint, request, render_template, jsonify, session
from app.db import get_db
from bson.objectid import ObjectId
import base64
import cv2
import numpy as np
import face_recognition

facerec_bp = Blueprint('facerec_bp', __name__)

# ✅ Route to show match face page (camera + match)
@facerec_bp.route('/match_face')
def match_face_page():
    return render_template('match_face.html')


# ✅ Route to open face registration page
@facerec_bp.route('/register-face-page')
def register_face_page():
    return render_template('register_face.html')


# ✅ Face Registration API
@facerec_bp.route('/register-face', methods=['POST'])
def register_face():
    data = request.json
    phone = data.get("phone")
    image_data = data.get("image")

    if not phone or not image_data:
        return jsonify({"success": False, "message": "Phone or image missing."})

    try:
        # Decode base64
        img_bytes = base64.b64decode(image_data.split(',')[1])
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_np is None:
            return jsonify({"success": False, "message": "Image decode failed. Possibly invalid format."})

        # Ensure image is 3-channel (RGB)
        if len(img_np.shape) != 3 or img_np.shape[2] != 3:
            return jsonify({"success": False, "message": "Image is not in expected RGB format."})

        rgb_img = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)

        # Detect and encode face
        encodings = face_recognition.face_encodings(rgb_img)
        if not encodings:
            return jsonify({"success": False, "message": "No face detected in image."})

        encoding = encodings[0].tolist()

        # Store in DB
        db = get_db()
        db.face_data.update_one(
            {"phone": phone},
            {"$set": {"encoding": encoding}},
            upsert=True
        )

        return jsonify({"success": True, "message": "✅ Face registered successfully!"})

    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Error during registration: {str(e)}"})


# ✅ Reusable verification logic
def verify_face_from_base64(phone, image_base64):
    db = get_db()
    record = db.face_data.find_one({"phone": phone})
    if not record or "encoding" not in record:
        return False, "❌ Face not registered. Please register first."

    try:
        # Decode and convert image
        input_bytes = base64.b64decode(image_base64.split(',')[1])
        input_np = np.frombuffer(input_bytes, np.uint8)
        input_img = cv2.imdecode(input_np, cv2.IMREAD_COLOR)

        if input_img is None:
            return False, "❌ Error decoding image"

        # Check if it’s valid 3-channel image
        if len(input_img.shape) != 3 or input_img.shape[2] != 3:
            return False, "❌ Unsupported image type. Must be RGB 3-channel image."

        rgb_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)

        # Get encoding from input image
        input_encodings = face_recognition.face_encodings(rgb_img)
        if not input_encodings:
            return False, "❌ No face detected in image."

        input_encoding = input_encodings[0]
        stored_encoding = np.array(record['encoding'])

        # Compare encodings
        match = face_recognition.compare_faces([stored_encoding], input_encoding)[0]
        return (True, "✅ Face verified!") if match else (False, "❌ Face does not match.")

    except Exception as e:
        return False, f"❌ Error during verification: {str(e)}"


# ✅ API endpoint for face verification
@facerec_bp.route('/verify-face', methods=['POST'])
def verify_face():
    data = request.get_json()
    image_data = data.get("image")

    if 'user_id' not in session or not image_data:
        return jsonify({"success": False, "message": "Not authenticated or image missing"})

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user:
        return jsonify({"success": False, "message": "User not found in session"})

    phone = user['phone']
    success, message = verify_face_from_base64(phone, image_data)
    return jsonify({"success": success, "message": message})
