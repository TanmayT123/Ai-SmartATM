from flask import Flask, redirect, url_for
from app.auth import auth_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# No prefix → allows /login, /register-face etc.
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return redirect(url_for('auth.login'))  # This will now work since /login exists

if __name__ == '__main__':
    app.run(debug=True)
