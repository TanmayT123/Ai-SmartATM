from flask import Flask, render_template
from app.auth import auth_bp

app = Flask(__name__, template_folder='templates')

# 🔐 Required to use session, flash, etc.
app.secret_key = 'your-super-secret-key-123!@#'  # Change to something more secure for production

# Registering authentication blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
