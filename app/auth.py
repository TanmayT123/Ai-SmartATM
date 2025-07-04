# app/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from bson.objectid import ObjectId
from app.db import get_db
from app.facerec import verify_face_from_base64, register_face_from_base64

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/', methods=['POST'])
def login():
    phone = request.form.get('phone')
    pin = request.form.get('pin')

    db = get_db()
    user = db.users.find_one({"phone": phone, "pin": pin})

    if user:
        session['user_id'] = str(user['_id'])
        flash("Login successful!", "success")
        return redirect(url_for('auth.dashboard'))
    else:
        flash("Invalid phone number or PIN", "flash")
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("You must log in first.", "flash")
        return redirect(url_for('auth.login_page'))

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})
    balance = user.get('balance', 0)
    return render_template('dashboard.html', balance=balance)

@auth_bp.route('/select-transaction/<type>')
def select_transaction(type):
    if type not in ['deposit', 'withdraw']:
        flash("Invalid transaction type", "flash")
        return redirect(url_for('auth.dashboard'))

    session['pending_transaction'] = type
    return redirect(url_for('auth.facial_auth'))

@auth_bp.route('/facial-auth')
def facial_auth():
    return render_template('facial_auth.html')

@auth_bp.route('/register-face', methods=['POST'])
def register_face():
    data = request.get_json()
    image_data = data.get('image')

    if not image_data:
        return jsonify({"success": False, "message": "No image received"})

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "User not logged in"})

    success = register_face_from_base64(image_data, user_id)
    if success:
        return jsonify({"success": True, "message": "Face registered successfully"})
    else:
        return jsonify({"success": False, "message": "No face detected"})

@auth_bp.route('/match-face', methods=['POST'])
def match_face():
    data = request.get_json()
    image_data = data.get('image')

    if not image_data:
        return jsonify({"success": False, "message": "No image received"})

    matched_user_id = verify_face_from_base64(image_data)

    if matched_user_id:
        session['user_id'] = matched_user_id
        redirect_url = url_for('auth.do_transaction', type=session.get('pending_transaction', 'deposit'))
        return jsonify({"success": True, "message": "Face matched!", "redirect_url": redirect_url})
    else:
        return jsonify({"success": False, "message": "Face not recognized"})

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

        session.pop('pending_transaction', None)
        return redirect(url_for('auth.dashboard'))

    return render_template('transaction.html', type=type)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('auth.login_page'))
