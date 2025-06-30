# app/auth.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from bson.objectid import ObjectId
from app.db import get_db
from app.facerec import verify_face_from_base64
import base64
import numpy as np

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        pin = request.form.get('pin')

        db = get_db()
        users = db['users']

        if users.find_one({'$or': [{'phone': phone}, {'email': email}]}):
            flash('User with this phone or email already exists.')
            return redirect(url_for('auth.register'))

        result = users.insert_one({
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'email': email,
            'pin': pin,
            'balance': 0
        })

        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        pin = request.form.get('pin')

        db = get_db()
        users = db['users']
        user = users.find_one({'phone': phone, 'pin': pin})

        if user:
            session['user_id'] = str(user['_id'])
            flash('Login successful!')
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid phone or PIN')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        db = get_db()
        users = db['users']
        user = users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            balance = user.get('balance', 0)
            return render_template('dashboard.html', balance=balance)
    flash("Please log in first.")
    return redirect(url_for('auth.login'))

@auth_bp.route('/face-auth', methods=['POST'])
def face_auth():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json()
    img_data = data.get('image')
    if not img_data:
        return jsonify({'success': False, 'message': 'No image provided'})

    # Extract base64 content from data URL
    img_str = img_data.split(',')[1]

    is_verified = verify_face_from_base64(session['user_id'], img_str)
    if is_verified:
        return jsonify({'success': True, 'message': 'Face verified! Redirecting to dashboard.'})
    else:
        return jsonify({'success': False, 'message': 'Face not recognized. Please try again.'})
