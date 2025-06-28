from flask import Flask
from app.auth import auth_bp
import os

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')
    )

    # ✅ Set the secret key for session and flash support
    app.secret_key = 'your_super_secret_key_here'  # Replace with a real random string

    app.register_blueprint(auth_bp)

    return app
