# app/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from bson.objectid import ObjectId
from app.db import get_db
from app.facerec import verify_face_from_base64, register_face_from_base64

auth_bp = Blueprint('auth', __name__)

# 🔹 Role selection landing page
@auth_bp.route('/select-role')
def select_role():
    return render_template('role_select.html')

# 🔹 USER LOGIN
@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    phone = request.form.get('phone')
    pin = request.form.get('pin')

    db = get_db()
    user = db.users.find_one({"phone": phone, "pin": pin})

    if user:
        session['user_id'] = str(user['_id'])
        session['phone'] = phone  # Used for face auth
        flash("Login successful!", "success")
        return redirect(url_for('auth.dashboard'))
    else:
        flash("Invalid phone number or PIN", "flash")
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login_page():
    db = get_db()

    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        pin = request.form.get('pin')

        # Check if user already exists
        existing_user = db.users.find_one({"phone": phone})
        if existing_user:
            flash("User already exists with this phone number", "flash")
            return redirect(url_for('auth.admin_login_page'))

        # Insert new user
        db.users.insert_one({
            "firstname": firstname,
            "lastname": lastname,
            "phone": phone,
            "email": email,
            "pin": pin,
            "balance": 0
        })

        # Redirect to bankdashboard.html after successful registration
        return render_template("bankdashboard.html", name=firstname)

    # If GET, just show the registration form
    return render_template('register.html')


# 🔹 USER REGISTRATION ➜ Creates account and redirects to bankdashboard.html
@auth_bp.route('/register', methods=['POST'])
def register_user():
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    phone = request.form.get('phone')
    email = request.form.get('email')
    pin = request.form.get('pin')

    db = get_db()

    # Optional: Check for existing user
    existing_user = db.users.find_one({"phone": phone})
    if existing_user:
        flash("User with this phone already exists", "flash")
        return redirect(url_for('auth.admin_login_page'))  # Show same register.html again

    # Insert new user
    db.users.insert_one({
        "firstname": firstname,
        "lastname": lastname,
        "phone": phone,
        "email": email,
        "pin": pin,
        "balance": 0
    })

    # Redirect to dashboard
    return render_template("bankdashboard.html", name=firstname)


# 🔹 USER DASHBOARD
@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("You must log in first.", "flash")
        return redirect(url_for('auth.login_page'))

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})
    balance = user.get('balance', 0)
    return render_template('dashboard.html', balance=balance)



# 🔹 SELECT TRANSACTION
@auth_bp.route('/select-transaction/<type>')
def select_transaction(type):
    if type not in ['deposit', 'withdraw']:
        flash("Invalid transaction type", "flash")
        return redirect(url_for('auth.dashboard'))

    session['pending_transaction'] = type
    return redirect(url_for('auth.facial_auth'))

# 🔹 FACIAL AUTH PAGE
@auth_bp.route('/facial-auth')
def facial_auth():
    if 'pending_transaction' not in session:
        flash("Transaction type not selected.", "flash")
        return redirect(url_for('auth.dashboard'))

    return render_template('facial_auth.html')

# 🔹 REGISTER FACE PAGE (GET)
@auth_bp.route('/register-face', methods=['GET'])
def register_face_page():
    return render_template('register_face.html')

# 🔹 REGISTER FACE (Capture + Save)
@auth_bp.route('/register-face', methods=['POST'])
def register_face():
    data = request.get_json()
    image_data = data.get('image')
    phone = data.get('phone')  # <-- get phone from JSON

    if not image_data:
        return jsonify({"success": False, "message": "No image received"})

    if not phone:
        return jsonify({"success": False, "message": "Phone number missing"})

    success = register_face_from_base64(image_data, phone)
    if success:
        return jsonify({"success": True, "message": "Face registered successfully"})
    else:
        return jsonify({"success": False, "message": "No face detected"})

# 🔹 VERIFY USER (for login)
@auth_bp.route('/verify-user', methods=['POST'])
def verify_user():
    data = request.get_json()
    phone = data.get('phone')
    pin = data.get('pin')

    db = get_db()
    user = db.users.find_one({"phone": phone, "pin": pin})

    if user:
        session['phone'] = phone  # Save phone in session
        return jsonify({"success": True, "message": "User verified"})
    else:
        return jsonify({"success": False, "message": "Invalid phone or PIN"})

# 🔹 MATCH FACE (for transaction auth)
@auth_bp.route('/match-face', methods=['POST'])
def match_face():
    data = request.get_json()
    image_data = data.get('image')

    if not image_data:
        return jsonify({"success": False, "message": "No image received"})

    matched_phone = verify_face_from_base64(image_data)

    if matched_phone:
        db = get_db()
        user = db.users.find_one({"phone": matched_phone})
        if user:
            session['user_id'] = str(user['_id'])
            session['phone'] = matched_phone

            redirect_url = url_for('auth.do_transaction', type=session.get('pending_transaction', 'deposit'))
            session.pop('pending_transaction', None)

            return jsonify({"success": True, "message": "Face matched!", "redirect_url": redirect_url})

    return jsonify({"success": False, "message": "Face not recognized"})

# 🔹 DO TRANSACTION
@auth_bp.route('/do-transaction/<type>', methods=['GET', 'POST'])
def do_transaction(type):
    if 'user_id' not in session:
        flash("Please login to continue", "flash")
        return redirect(url_for('auth.login_page'))

    if type not in ['deposit', 'withdraw']:
        flash("Invalid transaction type", "flash")
        return redirect(url_for('auth.dashboard'))

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})

    if request.method == 'POST':
        amount = int(request.form.get('amount', 0))

        if type == 'deposit':
            new_balance = user['balance'] + amount
            db.users.update_one({"_id": user['_id']}, {"$set": {"balance": new_balance}})
            flash(f"Deposited ₹{amount}", "success")

        elif type == 'withdraw':
            if amount > user['balance']:
                flash("Insufficient balance", "flash")
                return redirect(request.url)
            new_balance = user['balance'] - amount
            db.users.update_one({"_id": user['_id']}, {"$set": {"balance": new_balance}})
            flash(f"Withdrew ₹{amount}", "success")

        return redirect(url_for('auth.dashboard'))

    return render_template('transaction.html', type=type)

# 🔹 LOGOUT
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('auth.login_page'))
