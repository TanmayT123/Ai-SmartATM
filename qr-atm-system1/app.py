from flask import Flask, render_template
from app.auth import auth_bp

app = Flask(__name__, template_folder='templates')
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
