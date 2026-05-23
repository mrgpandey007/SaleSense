from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = "MRG007123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── SQLite Connection ─────────────────────────────────
def get_db():
    db = sqlite3.connect('salesense.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS user_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    db.commit()
    db.close()

with app.app_context():
    init_db()

# ── Login Required Decorator ─────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Get user upload folder ───────────────────────────
def get_user_folder():
    user_id = session.get("user_id")
    folder = os.path.join(app.config["UPLOAD_FOLDER"], str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_filepath():
    return os.path.join(get_user_folder(), "sales_data.csv")

# ── Home ─────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# ── Register ─────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm", "").strip()

        # ── 1. Empty field check ──
        if not username or not email or not password or not confirm:
            flash("All fields are required", "error")
            return redirect(url_for("register"))

        # ── 2. Username validation ──
        if len(username) < 3:
            flash("Username must be at least 3 characters", "error")
            return redirect(url_for("register"))

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash("Username can only contain letters, numbers and underscore", "error")
            return redirect(url_for("register"))

        # ── 3. Email structure check ──
        if "@" not in email or email.count("@") != 1:
            flash("Invalid email — must contain exactly one @", "error")
            return redirect(url_for("register"))

        local_part, domain_part = email.split("@")

        # Local part checks
        if len(local_part) < 2 or len(local_part) > 30:
            flash("Email username part is invalid", "error")
            return redirect(url_for("register"))

        if not re.match(r'^[a-zA-Z0-9._%+\-]+$', local_part):
            flash("Invalid characters in email", "error")
            return redirect(url_for("register"))

        # Domain must have a dot
        if "." not in domain_part:
            flash("Invalid email domain — missing dot", "error")
            return redirect(url_for("register"))

        # Split domain into name and TLD
        domain_parts = domain_part.split(".")
        domain_name  = domain_parts[0]
        tld          = domain_parts[-1]

        # Domain name must be 2 to 8 characters only
        # gmail=5, yahoo=5, hotmail=7 — strictly max 8
        if len(domain_name) < 2 or len(domain_name) > 8:
            flash("Invalid email — domain name too long or too short", "error")
            return redirect(url_for("register"))

        # Domain name must be letters/numbers/hyphens only
        if not re.match(r'^[a-zA-Z0-9\-]+$', domain_name):
            flash("Invalid email domain name", "error")
            return redirect(url_for("register"))

        # TLD must be exactly 2 to 3 characters only
        # com=3, in=2, org=3, net=3
        # Reject anything like com231, compouj etc
        if len(tld) < 2 or len(tld) > 3:
            flash("Invalid email — use a real TLD like .com or .in", "error")
            return redirect(url_for("register"))

        # TLD must be letters ONLY — no numbers allowed
        if not tld.isalpha():
            flash("Invalid email — TLD cannot contain numbers", "error")
            return redirect(url_for("register"))

        # Allowed TLD whitelist — strictly controlled
        allowed_tlds = {
            "com", "in", "org", "net", "edu",
            "gov", "io", "biz", "me", "co",
            "ac", "uk", "us", "au", "ca",
            "de", "fr", "jp", "nz", "za"
        }
        if tld.lower() not in allowed_tlds:
            flash("Invalid email — use a valid TLD like .com, .in, .org", "error")
            return redirect(url_for("register"))

        # Known valid domains whitelist
        known_domains = {
            "gmail", "yahoo", "hotmail", "outlook",
            "icloud", "rediff", "ymail", "live",
            "aol", "proton", "zoho", "college",
            "student", "mail", "inbox"
        }
        if domain_name.lower() not in known_domains:
            flash("Please use a valid email provider (gmail, yahoo, hotmail etc.)", "error")
            return redirect(url_for("register"))

        # Final full regex check
        email_regex = re.compile(
            r'^[a-zA-Z0-9._%+\-]{2,30}@[a-zA-Z0-9]{2,8}\.[a-zA-Z]{2,3}$'
        )
        if not email_regex.match(email):
            flash("Please enter a valid email address (e.g. name@gmail.com)", "error")
            return redirect(url_for("register"))

        # ── 4. Password validation ──
        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("register"))

        # ── 5. Save to Database ──
        try:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE username=? OR email=?",
                (username, email)
            ).fetchone()

            if existing:
                flash("Username or email already exists", "error")
                db.close()
                return redirect(url_for("register"))

            hashed = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed)
            )
            db.commit()
            db.close()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("register"))

    return render_template("register.html")

# ── Login ─────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter username and password", "error")
            return redirect(url_for("login"))

        try:
            db = get_db()
            user = db.execute(
                "SELECT id, username, password FROM users WHERE username=?",
                (username,)
            ).fetchone()
            db.close()

            if user and check_password_hash(user[2], password):
                session["user_id"]  = user[0]
                session["username"] = user[1]
                flash(f"Welcome back, {user[1]}!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password", "error")
                return redirect(url_for("login"))

        except Exception as e:
            flash(f"Database error: {str(e)}", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# ── Logout ────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

# ── Dashboard ─────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=session["username"])

# ── Upload ────────────────────────────────────────────
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "" or not file.filename.endswith(".csv"):
            flash("Please upload a valid CSV file", "error")
            return redirect(request.url)

        filepath = get_user_filepath()
        file.save(filepath)

        from utils.data_processor import process_csv
        result = process_csv(filepath)
        if result["success"]:
            session["data_loaded"] = True
            flash("File uploaded successfully!", "success")
            return redirect(url_for("predict"))
        else:
            flash(f"Error: {result['error']}", "error")

    return render_template("upload.html", user=session["username"])

# ── Predict ───────────────────────────────────────────
@app.route("/predict")
@login_required
def predict():
    return render_template("predict.html", user=session["username"])

# ── Charts ────────────────────────────────────────────
@app.route("/charts")
@login_required
def charts():
    return render_template("charts.html", user=session["username"])

# ── Confusion Matrix ──────────────────────────────────
@app.route("/confusion")
@login_required
def confusion():
    return render_template("confusion.html", user=session["username"])

# ── REST API ──────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    try:
        from utils.predictor import train_and_predict
        filepath = get_user_filepath()
        data     = request.get_json() or {}
        periods  = int(data.get("periods", 6))
        result   = train_and_predict(filepath, periods)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics", methods=["GET"])
@login_required
def api_metrics():
    try:
        from utils.predictor import get_model_metrics
        filepath = get_user_filepath()
        metrics  = get_model_metrics(filepath)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/chart-data", methods=["GET"])
@login_required
def api_chart_data():
    try:
        from utils.chart_data import generate_chart_data
        filepath   = get_user_filepath()
        chart_type = request.args.get("type", "monthly")
        data       = generate_chart_data(filepath, chart_type)
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/summary", methods=["GET"])
@login_required
def api_summary():
    try:
        from utils.data_processor import process_csv
        filepath = get_user_filepath()
        result   = process_csv(filepath)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/confusion-matrix", methods=["GET"])
@login_required
def api_confusion_matrix():
    try:
        from utils.confusion_matrix_plot import get_confusion_matrix_data
        filepath = get_user_filepath()
        result   = get_confusion_matrix_data(filepath)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Error Handlers ────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("404.html"), 500

# ── Run ───────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)