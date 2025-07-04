"""
Face‑recognition Blueprint
Stores each encoding under `user_id` == phone number
"""

from flask import Blueprint, request, render_template, jsonify
from app.db      import get_db
import base64, cv2, numpy as np, face_recognition
from datetime    import datetime

facerec_bp = Blueprint("facerec_bp", __name__, template_folder="../templates")


# ───────────────────────────────────────────────
# HTML page to capture face
# ───────────────────────────────────────────────
@facerec_bp.route("/register-face-page")
def register_face_page():
    return render_template("register_face.html")


# ───────────────────────────────────────────────
# Verify phone & PIN (AJAX before camera starts)
# ───────────────────────────────────────────────
@facerec_bp.route("/verify-user", methods=["POST"])
def verify_user():
    data  = request.get_json(silent=True) or {}
    phone = data.get("phone")
    pin   = data.get("pin")

    user = get_db().users.find_one({"phone": phone, "pin": pin})
    return jsonify({"success": bool(user)})


# ───────────────────────────────────────────────
# Register face → store encoding
# ───────────────────────────────────────────────
@facerec_bp.route("/register-face", methods=["POST"])
def register_face():
    data  = request.get_json(silent=True) or {}
    phone = data.get("phone")
    image = data.get("image")

    if not phone or not image:
        return jsonify({"success": False,
                        "message": "Phone & image required"}), 400

    # Decode Base64 → RGB numpy
    try:
        img_np = cv2.imdecode(
            np.frombuffer(base64.b64decode(image.split(",")[1]), np.uint8),
            cv2.IMREAD_COLOR
        )
        rgb_img = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"[ERROR] Decode failed: {e}")
        return jsonify({"success": False,
                        "message": "Invalid image"}), 400

    enc = face_recognition.face_encodings(rgb_img)
    if not enc:
        return jsonify({"success": False,
                        "message": "No face detected"}), 400

    db = get_db()
    db.face_encodings.update_one(
        {"user_id": phone},
        {"$set": {
            "user_id" : phone,
            "encoding": enc[0].tolist(),
            "updated" : datetime.utcnow()
        }},
        upsert=True
    )

    print(f"[INFO] Face registered for {phone}")
    return jsonify({"success": True,
                    "message": "Face registered successfully"})


# ───────────────────────────────────────────────
# Helper used by auth.py
# ───────────────────────────────────────────────
def verify_face_from_base64(phone: str, image_b64: str) -> bool:
    db = get_db()
    doc = db.face_encodings.find_one({"user_id": phone})
    if not doc:
        print("[DEBUG] No stored encoding for", phone)
        return False

    try:
        img_np = cv2.imdecode(
            np.frombuffer(base64.b64decode(image_b64.split(",")[1]), np.uint8),
            cv2.IMREAD_COLOR
        )
        rgb    = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"[ERROR] Verification decode failed: {e}")
        return False

    cand_enc = face_recognition.face_encodings(rgb)
    if not cand_enc:
        print("[DEBUG] No face detected in candidate frame")
        return False

    dist  = face_recognition.face_distance([np.array(doc["encoding"])],
                                           cand_enc[0])[0]
    match = dist < 0.6
    print(f"[DEBUG] {phone} dist={dist:.4f} → match={match}")
    return match


# ───────────────────────────────────────────────
# Web‑API endpoint for JS webcam calls
# ───────────────────────────────────────────────
@facerec_bp.route("/verify-face", methods=["POST"])
def verify_face():
    data  = request.get_json(silent=True) or {}
    phone = data.get("phone")
    image = data.get("image")

    if not phone or not image:
        return jsonify({"success": False,
                        "message": "Phone & image required"}), 400

    ok = verify_face_from_base64(phone, image)
    return jsonify({
        "success": ok,
        "message": "✅ Face matched!" if ok else "❌ Face did not match."
    })
