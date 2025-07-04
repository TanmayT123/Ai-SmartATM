# app.py

from flask import Flask, redirect, url_for
from app.auth import auth_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key'

app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return redirect(url_for('auth.select_role'))

if __name__ == '__main__':
    app.run(debug=True)
