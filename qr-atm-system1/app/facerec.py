from flask import Blueprint, request, render_template, jsonify
from app.db import get_db
import base64
import cv2
import numpy as np

facerec_bp = Blueprint('facerec_bp', __name__)

@facerec_bp.route('/register-face-page')
def register_face_page():
    return render_template('register_face.html')

@facerec_bp.route('/verify-user', methods=['POST'])
def verify_user():
    data = request.json
    phone = data.get('phone')
    pin = data.get('pin')

    db = get_db()
    user = db.users.find_one({"phone": phone, "pin": pin})
    return jsonify({"success": bool(user)})

@facerec_bp.route('/register-face', methods=['POST'])
def register_face():
    data = request.json
    phone = data.get("phone")
    image_data = data.get("image")

    # Decode base64 to image (optional - here just to validate)
    img_bytes = base64.b64decode(image_data.split(',')[1])
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    db = get_db()
    db.face_data.insert_one({
        "phone": phone,
        "image": image_data
    })
    return jsonify({"message": "Face registered successfully"})

def verify_face_from_base64(phone, image_base64):
    """
    Stub example for face verification by comparing with registered data.

    Args:
        phone (str): User phone number to find registered face.
        image_base64 (str): Base64 encoded face image to verify.

    Returns:
        bool: True if face matches, False otherwise.
    """
    db = get_db()
    user_face = db.face_data.find_one({"phone": phone})

    if not user_face:
        return False

    # Decode input image
    input_img_bytes = base64.b64decode(image_base64.split(',')[1])
    input_np_arr = np.frombuffer(input_img_bytes, np.uint8)
    input_img = cv2.imdecode(input_np_arr, cv2.IMREAD_COLOR)

    # Decode registered image
    reg_img_bytes = base64.b64decode(user_face["image"].split(',')[1])
    reg_np_arr = np.frombuffer(reg_img_bytes, np.uint8)
    reg_img = cv2.imdecode(reg_np_arr, cv2.IMREAD_COLOR)

    # Dummy check: compare image shapes
    if input_img.shape == reg_img.shape:
        return True
    return False
