from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from app.db   import get_db
from app.auth import auth_bp            # ← your Auth blueprint
import base64, numpy as np, cv2, face_recognition

app = Flask(__name__)
app.secret_key = "XYZEWQID1234567890"  # Change this to a secure key!

# ───────────────────────────────────────────────
# Blueprints
# ───────────────────────────────────────────────
app.register_blueprint(auth_bp, url_prefix="/")
# If you created a separate facerec_bp earlier, register it too:
from app.facerec import facerec_bp
app.register_blueprint(facerec_bp)

# ───────────────────────────────────────────────
# Home → Login
# ───────────────────────────────────────────────
@app.route("/")
def home():
    return redirect(url_for("auth.login"))

# ───────────────────────────────────────────────
# Dashboard & balance helpers
# ───────────────────────────────────────────────
def current_user():
    """Return Mongo user doc based on session, or None."""
    if "user_id" not in session:
        return None
    return get_db().users.find_one({"phone": session["user_id"]})


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        flash("Please log in first.")
        return redirect(url_for("auth.login"))

    return render_template(
        "dashboard.html",
        firstname=user.get("firstname", ""),
        lastname =user.get("lastname", ""),
        balance  =user.get("balance", 0)
    )


@app.route("/balance")
def check_balance():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", balance=user.get("balance", 0))

# ───────────────────────────────────────────────
# Face‑registration page (HTML)
# ───────────────────────────────────────────────
@app.route("/register-face-page")
def register_face_page():
    return render_template("register_face.html")

# ───────────────────────────────────────────────
# Verify phone+PIN (AJAX)
# ───────────────────────────────────────────────
@app.route("/verify-user", methods=["POST"])
def verify_user():
    data  = request.get_json(silent=True) or {}
    phone = data.get("phone")
    pin   = data.get("pin")

    ok = bool(get_db().users.find_one({"phone": phone, "pin": pin}))
    return jsonify({"success": ok})

# ───────────────────────────────────────────────
# Register face  →  stores {user_id, encoding}
# ───────────────────────────────────────────────
# ── Register‑face page  *and*  AJAX API in one route ─────────────
@app.route("/register-face", methods=["GET", "POST"])
def register_face():
    # ── 1.  User just visited the URL in the browser (GET)
    if request.method == "GET":
        return render_template("register_face.html")

    # ── 2.  Webcam JavaScript sent a JSON payload (POST)
    data   = request.get_json(force=True)
    phone  = data.get("phone")
    img_b64= data.get("image")

    if not phone or not img_b64:
        return jsonify({"message": "❌ Phone & image required"}), 400

    # ---------- decode + detect + encode exactly as before ----------
    import base64, cv2, numpy as np, face_recognition
    try:
        img_np = cv2.imdecode(
            np.frombuffer(base64.b64decode(img_b64.split(",")[1]), np.uint8),
            cv2.IMREAD_COLOR
        )
        rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    except Exception as e:
        return jsonify({"message": f"❌ Image decode failed: {e}"}), 400

    locs = face_recognition.face_locations(rgb)
    if not locs:
        return jsonify({"message": "❌ No face detected"}), 400

    enc  = face_recognition.face_encodings(rgb, locs)[0]

    db = get_db()
    db.face_encodings.update_one(
        {"user_id": phone},
        {"$set": {"user_id": phone, "encoding": enc.tolist()}},
        upsert=True
    )

    return jsonify({"message": "✅ Face registered successfully!"})


# ───────────────────────────────────────────────
# Helper for verification
# ───────────────────────────────────────────────
def verify_face_from_base64(phone: str, img_b64: str) -> bool:
    rec = get_db().face_encodings.find_one({"user_id": phone})
    if not rec:
        return False
    try:
        img_np = cv2.imdecode(
            np.frombuffer(base64.b64decode(img_b64.split(",")[1]), np.uint8),
            cv2.IMREAD_COLOR
        )
    except Exception:
        return False

    cand = face_recognition.face_encodings(img_np)
    if not cand:
        return False

    return face_recognition.compare_faces(
        [np.array(rec["encoding"])], cand[0], tolerance=0.6
    )[0]

# ───────────────────────────────────────────────
# Verify face  (AJAX from webcam)
# ───────────────────────────────────────────────
@app.route("/verify-face", methods=["POST"])
def verify_face():
    data  = request.get_json(force=True)
    phone = data.get("phone")
    img   = data.get("image")

    if not phone or not img:
        return jsonify({"success": False, "message": "Phone & image required"})

    ok = verify_face_from_base64(phone, img)
    return jsonify({"success": ok,
                    "message": "Face verified" if ok else "Face verification failed"})

# ───────────────────────────────────────────────
# Logout
# ───────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

# ───────────────────────────────────────────────
# Run in debug so you can see tracebacks
# ───────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)      # ⬅ returned to debug mode for development
