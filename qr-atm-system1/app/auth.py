# app/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.db import get_db

auth_bp = Blueprint('auth', __name__)
db = get_db()
users = db['users']

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form['phone']
        pin = request.form['pin']
        if users.find_one({'phone': phone}):
            flash('User already exists!')
        else:
            users.insert_one({'phone': phone, 'pin': pin, 'balance': 0})
            flash('Registration successful!')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        pin = request.form['pin']
        user = users.find_one({'phone': phone, 'pin': pin})
        if user:
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    return render_template('login.html')
