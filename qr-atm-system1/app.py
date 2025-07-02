from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from bson.objectid import ObjectId
from app.db import get_db
from app.auth import auth_bp
import base64
import numpy as np
import cv2
import face_recognition

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.register_blueprint(auth_bp, url_prefix='/')


@app.route('/')
def home():
    return redirect(url_for('auth.login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html', balance=None)
    return redirect(url_for('auth.login'))


@app.route('/balance')
def check_balance():
    if 'user_id' in session:
        db = get_db()
        user = db['users'].find_one({'_id': ObjectId(session['user_id'])})
        balance = user.get('balance', 0) if user else 0
        return render_template('dashboard.html', balance=balance)
    return redirect(url_for('auth.login'))


@app.route('/select_transaction/<action_type>')
def select_transaction(action_type):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if action_type.lower() not in ['deposit', 'withdraw']:
        return "Invalid transaction type", 404

    # Render a page where user can start webcam and verify face before proceeding
    return render_template('verify_face.html', action_type=action_type.lower())


@app.route('/deposit')
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    # Deposit page shown only after face verified via separate POST API
    return render_template('deposit.html')


@app.route('/withdraw')
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    # Withdraw page shown only after face verified via separate POST API
    return render_template('withdraw.html')


# Face registration page (GET)
@app.route('/register-face', methods=['GET'])
def register_face_page():
    return render_template('register_face.html')


# Verify phone and PIN (POST)
@app.route('/verify-user', methods=['POST'])
def verify_user():
    data = request.get_json()
    phone = data.get("phone")
    pin = data.get("pin")

    db = get_db()
    user = db.users.find_one({"phone": phone, "pin": pin})
    return jsonify({"success": bool(user)})


# Register face (POST)
@app.route('/register-face', methods=['POST'])
def register_face():
    try:
        data = request.get_json(force=True)
        phone = data.get("phone")
        image_data = data.get("image")

        if not image_data:
            return jsonify({"message": "❌ No image received."})

        try:
            img_bytes = base64.b64decode(image_data.split(',')[1])
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # ✅ Convert BGR to RGB for face_recognition
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        except Exception as e:
            return jsonify({"message": f"❌ Image decoding failed: {str(e)}"})

        # Detect face and encode
        face_locations = face_recognition.face_locations(img_rgb)
        if not face_locations:
            return jsonify({"message": "❌ No face detected."})

        face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]

        db = get_db()
        # Remove old encoding for this phone if any, then insert new
        db.face_data.delete_many({"phone": phone})
        db.face_data.insert_one({
            "phone": phone,
            "encoding": face_encoding.tolist()
        })

        return jsonify({"message": "✅ Face registered successfully!"})
    
    except Exception as e:
        return jsonify({"message": f"❌ Exception: {str(e)}"})



# Face verification helper function
def verify_face_from_base64(phone, image_base64):
    db = get_db()
    record = db.face_data.find_one({"phone": phone})
    if not record:
        return False

    try:
        # Decode incoming image
        input_bytes = base64.b64decode(image_base64.split(',')[1])
        input_np = np.frombuffer(input_bytes, np.uint8)
        input_img = cv2.imdecode(input_np, cv2.IMREAD_COLOR)

        input_encodings = face_recognition.face_encodings(input_img)
        if not input_encodings:
            return False
        input_encoding = input_encodings[0]

        stored_encoding = np.array(record['encoding'])

        # Compare faces with tolerance=0.6 (default)
        matches = face_recognition.compare_faces([stored_encoding], input_encoding)
        return matches[0]
    except Exception:
        return False


# API route for frontend to POST face image + phone and get verification result
@app.route('/verify-face', methods=['POST'])
def verify_face():
    data = request.get_json()
    phone = data.get('phone')
    image_data = data.get('image')

    if not phone or not image_data:
        return jsonify({"success": False, "message": "Phone and image required"})

    verified = verify_face_from_base64(phone, image_data)
    if verified:
        return jsonify({"success": True, "message": "Face verified"})
    else:
        return jsonify({"success": False, "message": "Face verification failed"})

from app.facerec import facerec_bp
app.register_blueprint(facerec_bp)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, threaded=False)

 # this was been used previously [app.run(debug=True)] in the upper line