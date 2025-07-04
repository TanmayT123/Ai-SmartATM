from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from app.db import get_db
from app.facerec import register_face_from_base64, verify_face_from_base64

auth_bp = Blueprint("auth", __name__)

# ───────────────────────────────────────────
# 1.  LOGIN
# ───────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        pin   = request.form.get("pin")

        user = get_db()["users"].find_one({"phone": phone, "pin": pin})
        if user:
            session["phone"] = phone
            flash("Login successful!", "success")
            return redirect(url_for("auth.dashboard"))

        flash("❌  Incorrect phone or PIN", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

# ───────────────────────────────────────────
# 2.  DASHBOARD
# ───────────────────────────────────────────
@auth_bp.route("/dashboard")
def dashboard():
    if "phone" not in session:
        return redirect(url_for("auth.login"))

    user  = get_db()["users"].find_one({"phone": session["phone"]})
    balance = user.get("balance", 0) if user else 0
    return render_template("dashboard.html", balance=balance)

# ───────────────────────────────────────────
# 3.  SELECT TRANSACTION  (Deposit | Withdraw)
# ───────────────────────────────────────────
@auth_bp.route("/select-transaction")
def select_transaction():
    if "phone" not in session:
        return redirect(url_for("auth.login"))

    tx_type = request.args.get("type", "deposit").lower()
    session["pending_tx_type"] = tx_type          #  <-- remember choice
    return render_template("select_transaction.html",
                           tx_type=tx_type.capitalize())

# ───────────────────────────────────────────
# 4.  FACIAL‑AUTH  (HTML page is still yours)
# ───────────────────────────────────────────
@auth_bp.route("/facial-auth")
def facial_auth():
    if "phone" not in session:
        return redirect(url_for("auth.login"))
    return render_template("facial_auth.html")

# ───────────────────────────────────────────
# 5.  FACE ➜ REGISTER  (unchanged)
# ───────────────────────────────────────────
@auth_bp.route("/register-face", methods=["POST"])
def register_face():
    data  = request.get_json()
    image = data.get("image")
    user_id = session.get("phone")

    if not image or not user_id:
        return jsonify({"success": False, "message": "Missing data"})

    ok = register_face_from_base64(image, user_id)
    return jsonify({"success": ok,
                    "message": "Face registered!" if ok
                               else "No face detected."})

# ───────────────────────────────────────────
# 6.  FACE ➜ VERIFY   (returns where to go next)
# ───────────────────────────────────────────
@auth_bp.route("/match-face", methods=["POST"])
def match_face():
    data  = request.get_json()
    image = data.get("image")

    if not image:
        return jsonify({"success": False, "message": "No image provided"})

    if verify_face_from_base64(image):
        # success → send next‑page URL back to browser
        return jsonify({
            "success": True,
            "message": "Face matched – proceed",
            "next": url_for("auth.amount")     # <‑‑ new !
        })

    return jsonify({"success": False,
                    "message": "Face did not match. Try again."})

# ───────────────────────────────────────────
# 7.  AMOUNT PAGE  (deposit / withdraw)
# ───────────────────────────────────────────
@auth_bp.route("/amount", methods=["GET", "POST"])
def amount():
    if "phone" not in session or "pending_tx_type" not in session:
        return redirect(url_for("auth.dashboard"))

    tx_type = session["pending_tx_type"]   # deposit | withdraw

    if request.method == "POST":
        # -- validate amount -------------------------
        try:
            amount = float(request.form.get("amount", "0"))
            assert amount > 0
        except (ValueError, AssertionError):
            flash("Enter a positive amount", "error")
            return redirect(url_for("auth.amount"))

        db     = get_db()
        users  = db["users"]
        phone  = session["phone"]
        user   = users.find_one({"phone": phone})

        if not user:
            flash("User not found", "error")
            return redirect(url_for("auth.logout"))

        # -- DEPOSIT ---------------------------------
        if tx_type == "deposit":
            users.update_one({"phone": phone}, {"$inc": {"balance": amount}})
            flash(f"₹{amount} deposited!", "success")

        # -- WITHDRAW --------------------------------
        else:
            current_bal = user.get("balance", 0)
            if current_bal < amount:
                flash("Insufficient balance", "error")
                return redirect(url_for("auth.amount"))

            users.update_one({"phone": phone}, {"$inc": {"balance": -amount}})
            flash(f"₹{amount} withdrawn!", "success")

        # done, forget the pending txn
        session.pop("pending_tx_type", None)
        return redirect(url_for("auth.dashboard"))

    # GET → show the form
    return render_template("amount.html", tx_type=tx_type.capitalize())
