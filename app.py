from flask import Flask, redirect, url_for
from app.auth import auth_bp  # Importing your existing auth blueprint

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Register auth blueprint without prefix (so /register-face, /match-face, etc. work)
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    # Redirect root to the facial auth page at auth_bp's "/"
    return redirect(url_for('auth.facial_auth_page'))

if __name__ == '__main__':
    app.run(debug=True)
