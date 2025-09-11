# WARNING: For production, switch to HTTP-only, Secure cookies for JWT tokens!

import os
import pandas as pd
import mysql.connector
import functools
import itsdangerous

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired  # for generating and verifying tokens
from werkzeug.security import generate_password_hash, check_password_hash  # for password hashing
from flask import Flask, request, jsonify

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_cors import CORS
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier ,GradientBoostingClassifier,AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from datetime import timedelta
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

from dotenv import load_dotenv
load_dotenv("apppass.env")

app = Flask(__name__)




# Fix CORS configuration - allow multiple origins and be more permissive for development
CORS(
    app,
    resources={r"/*": {"origins": ["http://127.0.0.1:5500", "http://127.0.0.1:5501", "http://localhost:5500", "http://localhost:5501", "http://127.0.0.1:3000", "http://localhost:3000"]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-me-in-prod")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)

serializer = URLSafeTimedSerializer(app.config["JWT_SECRET_KEY"])

jwt = JWTManager(app)

def get_user_by_email(conn, email):
    with conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT id, email, full_name, password_hash, is_admin FROM users WHERE email=%s", (email,))
        return cur.fetchone()

def get_user_by_id(conn, user_id):
    with conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT id, email, full_name, is_admin FROM users WHERE id=%s", (user_id,))
        return cur.fetchone()

def admin_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get("is_admin"):
            return {"message": "Admins only."}, 403
        return fn(*args, **kwargs)
    return wrapper

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("NITROGEN35", ""), 
        database="crop_system",
        auth_plugin="mysql_native_password"
    )

# === Load dataset and train models ===
df = pd.read_csv("Crop_recommendation.csv")
X = df.drop('label', axis=1)
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


rf_model = RandomForestClassifier()
dt_model = DecisionTreeClassifier()
svm_model = SVC()
lr_model = LogisticRegression()
nb_model = GaussianNB()
knn_model = KNeighborsClassifier()
gb_model = GradientBoostingClassifier()
ada_model = AdaBoostClassifier()

rf_model.fit(X_train, y_train)
dt_model.fit(X_train, y_train)
svm_model.fit(X_train, y_train)
lr_model.fit(X_train, y_train)
nb_model.fit(X_train, y_train)
knn_model.fit(X_train, y_train)
gb_model.fit(X_train, y_train)
ada_model.fit(X_train, y_train)

# === Accuracy calculation (for reference) ===

rf_acc = round(accuracy_score(y_test, rf_model.predict(X_test)) * 100, 2)
dt_acc = round(accuracy_score(y_test, dt_model.predict(X_test)) * 100, 2)
svm_acc = round(accuracy_score(y_test, svm_model.predict(X_test)) * 100, 2)
lr_acc = round(accuracy_score(y_test, lr_model.predict(X_test)) * 100, 2)
nb_acc = round(accuracy_score(y_test, nb_model.predict(X_test)) * 100, 2)
knn_acc = round(accuracy_score(y_test, knn_model.predict(X_test)) * 100, 2)
gb_acc = round(accuracy_score(y_test, gb_model.predict(X_test)) * 100, 2)
ada_acc = round(accuracy_score(y_test, ada_model.predict(X_test)) * 100 , 2)

print("[MODEL ACCURACIES] RF:", rf_acc, "DT:", dt_acc, "SVM:", svm_acc, "LR:", lr_acc, "NB:", nb_acc, "KNN:", knn_acc, "GB:", gb_acc, "ADA:", ada_acc)

#======Update /predict endpoint=======#
@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json or {}
    # required fields validation
    req = ['N','P','K','temperature','humidity','ph','rainfall']
    for r in req:
        if r not in data:
            return jsonify({"error": f"Missing field: {r}"}), 400
    try:
        # Prepare input
        input_df = pd.DataFrame([[

           float(data['N']), float(data['P']), float(data['K']),
           float(data['temperature']), float(data['humidity']),
           float(data['ph']), float(data['rainfall'])
       ]], columns=X.columns)

        input_scaled = scaler.transform(input_df)
       # Predictions
        predictions = {
           "random_forest": rf_model.predict(input_scaled)[0],
           "decision_tree": dt_model.predict(input_scaled)[0],
           "svm": svm_model.predict(input_scaled)[0],
           "logistic_regression": lr_model.predict(input_scaled)[0],
           "naive_bayes": nb_model.predict(input_scaled)[0],
            "knn": knn_model.predict(input_scaled)[0],
            "gradient_boost": gb_model.predict(input_scaled)[0],
            "adaboost": ada_model.predict(input_scaled)[0]
        }
        accuracies = {
            "random_forest": rf_acc,
            "decision_tree": dt_acc,
            "svm": svm_acc,
            "logistic_regression": lr_acc,
            "naive_bayes": nb_acc,
            "knn": knn_acc,
            "gradient_boost": gb_acc,
            "adaboost": ada_acc}
        best_model = max(accuracies, key=accuracies.get)
        best_crop = predictions[best_model]
        # Persist to DB if user_id provided (extend columns)
        user_id = data.get("user_id")
        if user_id:
            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO predictions
                    (user_id, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall,
                     predicted_crop, rf_crop, dt_crop, svm_crop, lr_crop, knn_crop, nb_crop, gb_crop, ada_crop, best_model)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    user_id,
                    float(data['N']), float(data['P']), float(data['K']),
                    float(data['temperature']), float(data['humidity']),
                    float(data['ph']), float(data['rainfall']),
                    best_crop,
                    predictions['random_forest'], predictions['decision_tree'], predictions['svm'],
                    predictions['logistic_regression'], predictions['knn'], predictions['naive_bayes'],
                    predictions['gradient_boost'], predictions['adaboost'],
                    best_model
                ))
                db.commit()
                cursor.close()
                db.close()
            except Exception as e:
                # Warn but continue returning prediction
                print("[WARN] failed to save prediction:", e)

        # Return results
        return jsonify({
            "predictions": predictions,
            "accuracies": accuracies,
            "best_model": best_model,
            "best_crop": best_crop,
            "recommended_crop": best_crop
        })

    except Exception as e:
        print("[ERROR] /predict failed:", e)
        return jsonify({"error": str(e)}), 400
       


@app.route('/')
def home():
    return "Crop Predictor API is running ✅"

def is_valid_email(email):
    import re
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return '', 200
    data = request.json
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')
    # ... (validation as before) ...
    hashed_password = generate_password_hash(password)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409
        cursor.execute("INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)", (full_name, email, hashed_password))
        db.commit()
        user_id = cursor.lastrowid
        return jsonify({"message": "User registered successfully", "user_id": user_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == 'OPTIONS': return '', 200
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    try:
        conn = get_db()
        user = get_user_by_email(conn, email)
        if not user or not check_password_hash(user["password_hash"], password):
            conn.close()
            return jsonify({"error": "Invalid email or password"}), 401
        claims = {"is_admin": bool(user["is_admin"])}
        access_token = create_access_token(identity=str(user["id"]), additional_claims=claims)
        refresh_token = create_refresh_token(identity=str(user["id"]), additional_claims=claims)
        conn.close()
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "is_admin": bool(user["is_admin"])
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    # --- Password reset: Send Email ---
def send_reset_email(to_email, reset_link):
    """
    Send a password reset email using SMTP credentials from environment.
    Returns (True, "") on success, or (False, "error message") on failure.
    """
    try:
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 465))

        if not (smtp_user and smtp_pass):
            msg = "[WARN] SMTP credentials missing in environment; email not sent."
            print(msg, "Reset link:", reset_link)
            return False, msg

        # Build the message
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = "Crop Estimator - Password Reset"
        body = f"""Hi,

We received a request to reset your Crop Estimator password.

Click the link below to set a new password (valid for 15 minutes):
{reset_link}

If you didn't request this, you can ignore this email.

— Crop Estimator
"""
        msg.attach(MIMEText(body, "plain"))

        # Use SSL transport for port 465
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())

        print(f"[DEBUG] Reset email sent to {to_email}")
        return True, ""
    except Exception as e:
        err = str(e)
        print(f"[ERROR] Failed to send reset email: {err}")
        return False, err


#============ Forgot Password ============#
@app.route('/forgot_password', methods=['POST', 'OPTIONS'])
def forgot_password():
    if request.method == 'OPTIONS': return '', 200
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    try:
        conn = get_db()
        user = get_user_by_email(conn, email)
        conn.close()
        if not user:
            return jsonify({'error': 'Email not found'}), 404
        token = serializer.dumps({"user_id": user["id"]})
        reset_link = f"http://127.0.0.1:5500/reset_password.html?token={token}"
        # Send reset link to user's email
        sent, msg = send_reset_email(email, reset_link)
        if not sent:
            return jsonify({'error': 'Failed to send email: ' + msg}), 500
        return jsonify({"message": f"Password reset link sent to {email}."})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route("/token/refresh", methods=["POST", "OPTIONS"])
@jwt_required(refresh=True)
def refresh():
    if request.method == 'OPTIONS':
        return '', 200
    claims = get_jwt()
    identity = get_jwt_identity()
    new_access = create_access_token(identity=identity,
                                 additional_claims={"is_admin": claims.get("is_admin", False)})
    return {"access_token": new_access}, 200

@app.route('/history/<int:user_id>', methods=['GET', 'OPTIONS'])
def history(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM predictions WHERE user_id=%s ORDER BY created_at DESC LIMIT 10", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route('/history/all', methods=['GET', 'OPTIONS'])
def history_all():
    if request.method == 'OPTIONS':
        return '', 200
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM predictions ORDER BY created_at DESC LIMIT 100")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route('/change_password', methods=['POST', 'OPTIONS'])
def change_password():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT password_hash FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    if not user or not check_password_hash(user['password_hash'], old_password):
        cursor.close()
        db.close()
        return jsonify({'error': 'Old password incorrect'}), 401
    new_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({'message': 'Password updated successfully'})

#=========== RESET PASSWORD ============#

@app.route('/reset_password', methods=['POST', 'OPTIONS'])
def reset_password():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password is required'}), 400
    
    try:
        token_data = serializer.loads(token, max_age=900)
        user_id = token_data['user_id']
        new_hash = generate_password_hash(new_password)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Password reset successfully'})
    except SignatureExpired:
        return jsonify({"error": "Reset link expired"}), 400
    except BadSignature:
        return jsonify({"error": "Invalid reset link"}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500  
    
    

@app.route('/update_profile', methods=['POST', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    user_id = data.get('user_id')
    full_name = data.get('full_name')
    email = data.get('email')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email=%s AND id!=%s", (email, user_id))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return jsonify({'error': 'Email already in use'}), 409
    cursor.execute("UPDATE users SET full_name=%s, email=%s WHERE id=%s", (full_name, email, user_id))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/admin/users', methods=['GET', 'OPTIONS'])
@jwt_required()
@admin_required
def admin_users():
    if request.method == 'OPTIONS':
        return '', 200
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, full_name, email, created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s", (per_page, offset))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route('/admin/predictions', methods=['GET', 'OPTIONS'])
@jwt_required()
@admin_required
def admin_predictions():
    if request.method == 'OPTIONS':
        return '', 200
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM predictions ORDER BY created_at DESC LIMIT %s OFFSET %s", (per_page, offset))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

# Add error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)