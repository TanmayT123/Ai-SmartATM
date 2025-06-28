from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from app.db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form['phone']
        pin = request.form['pin']
        db = get_db()
        users = db['users']
        if users.find_one({'phone': phone}):
            flash('User already exists')
            return redirect(url_for('auth.register'))
        users.insert_one({'phone': phone, 'pin': pin})
        flash('Registration successful!')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        pin = request.form['pin']
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
        return '<h2>Welcome to the ATM Dashboard!</h2>'
    return redirect(url_for('auth.login'))
