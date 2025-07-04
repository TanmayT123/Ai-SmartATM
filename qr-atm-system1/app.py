from flask import Flask, redirect, url_for
from app.auth import auth_bp          # your existing blueprint

app = Flask(__name__)
app.secret_key = "CHANGE‑ME‑TO‑SOMETHING‑SECRET"

# Register all routes from auth.py (login, dashboard, face auth, …)
app.register_blueprint(auth_bp)

@app.route("/")
def home():
    # First page a user ever sees → Login
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    app.run(debug=True)      # remove debug=True in production
