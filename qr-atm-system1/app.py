from flask import Flask, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from app.db import get_db  # Ensure this is defined to connect to MongoDB
from app.auth import auth_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secure secret key
app.register_blueprint(auth_bp, url_prefix='/')

@app.route('/')
def home():
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html')
    return redirect(url_for('auth.login'))

@app.route('/balance')
def check_balance():
    if 'user_id' in session:
        db = get_db()
        user = db['users'].find_one({'_id': ObjectId(session['user_id'])})
        balance = user.get('balance', 0) if user else 0
        return render_template('dashboard.html', balance=balance)
    return redirect(url_for('auth.login'))

# Optional: logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)
