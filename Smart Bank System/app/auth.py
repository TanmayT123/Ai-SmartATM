"""
Auth Blueprint
* session['user_id'] is now the **phone number**
"""

from flask import (
    Blueprint, request, render_template, redirect,
    url_for, flash, session, jsonify
)
from app.db      import get_db
from app.facerec import verify_face_from_base64

auth_bp = Blueprint("auth", __name__)


# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────
def current_user():
    if "user_id" not in session:
        return None
    return get_db().users.find_one({"phone": session["user_id"]})


# ───────────────────────────────────────────────
# Routes
# ───────────────────────────────────────────────
@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = {k: request.form.get(k) for k in
                ("firstname", "lastname", "phone", "email", "pin")}
        db   = get_db()

        # Duplicate check
        if db.users.find_one({"$or": [{"phone": data["phone"]},
                                      {"email": data["email"]}]}):
            flash("Phone or email already exists.")
            return redirect(url_for("auth.register"))

        data["balance"] = 0
        db.users.insert_one(data)
        flash("Registration successful! Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        pin   = request.form.get("pin")

        user = get_db().users.find_one({"phone": phone, "pin": pin})
        if user:
            session["user_id"] = phone             # ← phone, not ObjectId
            flash("Login successful!")
            return redirect(url_for("auth.dashboard"))

        flash("Invalid phone or PIN")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/dashboard")
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


# ───────────────────────────────────────────────
# Facial‑auth flow
# ───────────────────────────────────────────────
@auth_bp.route("/facial-auth")
def facial_auth_page():
    if not current_user():
        flash("Please log in first.")
        return redirect(url_for("auth.login"))
    return render_template("match_face.html")


@auth_bp.route("/match-face", methods=["POST"])
def match_face():
    if not current_user():
        return jsonify({"success": False, "message": "Not logged in"})

    img = (request.get_json() or {}).get("image")
    if not img:
        return jsonify({"success": False, "message": "No image provided"})

    ok = verify_face_from_base64(session["user_id"], img)
    return jsonify({
        "success": ok,
        "message": "Face verified!" if ok else "Face does not match."
    })
