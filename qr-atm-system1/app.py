from flask import Flask, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from app.db import get_db
from app.auth import auth_bp
from app.facerec import verify_face_from_base64

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

    return render_template('select_transaction.html', action_type=action_type.lower())

@app.route('/deposit')
def deposit():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db['users'].find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return redirect('/login')

    username = user.get('username')
    if username and verify_face(username):
        return render_template('deposit.html')
    return "❌ Face verification failed."

@app.route('/withdraw')
def withdraw():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db['users'].find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return redirect('/login')

    username = user.get('username')
    if username and verify_face(username):
        return render_template('withdraw.html')
    return "❌ Face verification failed."

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)