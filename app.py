# WARNING: For production, switch to HTTP-only, Secure cookies for JWT tokens!

import os
import pandas as pd
import mysql.connector
import functools

from werkzeug.security import generate_password_hash, check_password_hash  # for password hashing
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

from datetime import timedelta
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

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

rf_model = RandomForestClassifier()
dt_model = DecisionTreeClassifier()
svm_model = SVC()

rf_model.fit(X_train, y_train)
dt_model.fit(X_train, y_train)
svm_model.fit(X_train, y_train)

# === Accuracy calculation (for reference) ===
rf_acc = round(accuracy_score(y_test, rf_model.predict(X_test)) * 100, 2)
dt_acc = round(accuracy_score(y_test, dt_model.predict(X_test)) * 100, 2)
svm_acc = round(accuracy_score(y_test, svm_model.predict(X_test)) * 100, 2)

@app.route('/')
def home():
    return "Crop Predictor API is running ✅"

# Add explicit OPTIONS handling for all routes
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    user_id = data.get("user_id")
    print("[DEBUG] Received JSON:", data)

    try:
        # Create dataframe for prediction
        input_data = pd.DataFrame([[
            data['N'],
            data['P'],
            data['K'],
            data['temperature'],
            data['humidity'],
            data['ph'],
            data['rainfall']
        ]], columns=X.columns)

        # Predict using all 3 models
        rf_result = rf_model.predict(input_data)[0]
        dt_result = dt_model.predict(input_data)[0]
        svm_result = svm_model.predict(input_data)[0]

        # Accuracy dictionary
        accuracies = {
            "random_forest": rf_acc,
            "decision_tree": dt_acc,
            "svm": svm_acc
        }

        predictions = {
            "random_forest": rf_result,
            "decision_tree": dt_result,
            "svm": svm_result
        }

        # Select best crop based on best model accuracy
        best_model = max(accuracies, key=accuracies.get)
        best_crop = predictions[best_model]

        # Store in database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO predictions 
            (user_id, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, predicted_crop, rf_crop, dt_crop, svm_crop, best_model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            data['N'], data['P'], data['K'],
            data['temperature'], data['humidity'],
            data['ph'], data['rainfall'],
            best_crop,
            rf_result,
            dt_result,
            svm_result,
            best_model
        ))
        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            "random_forest": rf_result,
            "decision_tree": dt_result,
            "svm": svm_result,
            "accuracies": accuracies,
            "recommended_crop": best_crop
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def is_valid_email(email):
    import re
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')

    if not (full_name and email and password):
        return jsonify({'error': 'Missing required fields'}), 400
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email address'}), 400
    if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'error': 'Password must be at least 8 chars, one uppercase, one number'}), 400

    hashed_password = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return jsonify({'error': 'Email already registered'}), 409
        cursor.execute("INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                       (full_name, email, hashed_password))
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
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    print(f"[DEBUG] Login attempt for email: {email}")

    try:
        conn = get_db()
        user = get_user_by_email(conn, email)
        print("[DEBUG] User found:", user)

        if not user or not check_password_hash(user["password_hash"], password):
            conn.close()
            return {"message": "Invalid email or password"}, 401

        claims = {"is_admin": bool(user["is_admin"])}
        access_token = create_access_token(identity=str(user["id"]), additional_claims=claims)
        refresh_token = create_refresh_token(identity=str(user["id"]), additional_claims=claims)

        conn.close()
        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "is_admin": bool(user["is_admin"]),
            },
        }, 200
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return {"message": "Something went wrong"}, 500
    
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

@app.route('/reset_password', methods=['POST', 'OPTIONS'])
def reset_password():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        db.close()
        return jsonify({'error': 'Email not found'}), 404
    new_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash=%s WHERE email=%s", (new_hash, email))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({'message': 'Password reset successful'})

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