from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from app.facerec import register_face_from_base64, verify_face_from_base64

auth_bp = Blueprint('auth', __name__)

# -------------------------------
# Landing page — Facial Auth UI
# -------------------------------
@auth_bp.route('/')
def facial_auth_page():
    if 'phone' not in session:
        session['phone'] = '9028611351'  # TEMP SET — in real app, do after login
    return render_template('facial_auth.html')

# -------------------------------
# Route to register face
# -------------------------------
@auth_bp.route('/register-face', methods=['POST'])
def register_face():
    data = request.get_json()
    image = data.get('image')
    user_id = session.get('phone')

    if not image:
        return jsonify({'success': False, 'message': 'No image provided'})
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    success = register_face_from_base64(image, user_id)
    if success:
        return jsonify({'success': True, 'message': 'Face registered successfully'})
    else:
        return jsonify({'success': False, 'message': 'Face registration failed. No face detected.'})

# -------------------------------
# Route to match face
# -------------------------------
@auth_bp.route('/match-face', methods=['POST'])
def match_face():
    data = request.get_json()
    image = data.get('image')

    if not image:
        return jsonify({'success': False, 'message': 'No image provided'})

    success = verify_face_from_base64(image)
    if success:
        return jsonify({'success': True, 'message': 'Face matched successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Face did not match. Try again.'})
