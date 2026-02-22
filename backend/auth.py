import jwt
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set! Add it to backend/.env\n"
        "Generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

ACCESS_TOKEN_EXPIRES  = timedelta(hours=1)
REFRESH_TOKEN_EXPIRES = timedelta(days=7)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    """SHA-256 hash. Acceptable for academic project."""
    return hashlib.sha256(password.encode()).hexdigest()


def make_token(user_id: int, is_admin: bool, expires: timedelta) -> str:
    payload = {
        "user_id":  user_id,
        "is_admin": is_admin,
        "exp":      datetime.utcnow() + expires,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """Extract and validate user from Authorization: Bearer <token> header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return decode_token(auth[len("Bearer "):])


def require_admin():
    """Return user dict if admin, else None."""
    user = get_current_user()
    return user if user and user.get("is_admin") else None


# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data      = request.get_json(force=True) or {}
    full_name = data.get("fullName", "").strip()
    email     = data.get("email", "").strip().lower()
    password  = data.get("password", "")

    if not full_name or not email or not password:
        return jsonify({"error": "fullName, email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    pw_hash = hash_password(password)

    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, pw_hash)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Account created successfully"})


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json(force=True) or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    pw_hash = hash_password(password)

    try:
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, full_name, email, is_admin FROM users WHERE email=%s AND password_hash=%s",
            (email, pw_hash)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    access_token  = make_token(user["id"], bool(user["is_admin"]), ACCESS_TOKEN_EXPIRES)
    refresh_token = make_token(user["id"], bool(user["is_admin"]), REFRESH_TOKEN_EXPIRES)

    return jsonify({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user": {
            "id":        user["id"],
            "full_name": user["full_name"],
            "email":     user["email"],
            "is_admin":  bool(user["is_admin"]),
        }
    })


# ─────────────────────────────────────────────
# REFRESH TOKEN
# ─────────────────────────────────────────────
@auth_bp.route("/token/refresh", methods=["POST"])
def refresh():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Refresh token required"}), 401
    payload = decode_token(auth[len("Bearer "):])
    if not payload:
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    new_access = make_token(payload["user_id"], payload["is_admin"], ACCESS_TOKEN_EXPIRES)
    return jsonify({"access_token": new_access})


# ─────────────────────────────────────────────
# FORGOT PASSWORD
# ─────────────────────────────────────────────
@auth_bp.route("/forgot_password", methods=["POST"])
def forgot_password():
    data  = request.get_json(force=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    reset_token = secrets.token_urlsafe(32)
    expires_at  = datetime.utcnow() + timedelta(hours=1)

    try:
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        if not user:
            cur.close()
            conn.close()
            return jsonify({"message": "If that email exists, a reset link has been sent."})

        cur.execute(
            "UPDATE users SET reset_token=%s, reset_token_expires=%s WHERE id=%s",
            (reset_token, expires_at, user["id"])
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    reset_link = f"http://127.0.0.1:5500/indexl.html?token={reset_token}"
    return jsonify({"message": "Reset link generated.", "reset_link": reset_link})


# ─────────────────────────────────────────────
# RESET PASSWORD
# ─────────────────────────────────────────────
@auth_bp.route("/reset_password", methods=["POST"])
def reset_password():
    data         = request.get_json(force=True) or {}
    token        = data.get("token", "")
    new_password = data.get("new_password", "")

    if not token or not new_password:
        return jsonify({"error": "Token and new password are required"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    try:
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, reset_token_expires FROM users WHERE reset_token=%s", (token,)
        )
        user = cur.fetchone()
        if not user:
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid or expired reset token"}), 400

        if datetime.utcnow() > user["reset_token_expires"]:
            cur.close()
            conn.close()
            return jsonify({"error": "Reset token has expired"}), 400

        pw_hash = hash_password(new_password)
        cur.execute(
            "UPDATE users SET password_hash=%s, reset_token=NULL, reset_token_expires=NULL WHERE id=%s",
            (pw_hash, user["id"])
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "Password reset successfully"})


# ─────────────────────────────────────────────
# LOGOUT  (client deletes tokens; server confirms)
# ─────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logged out"})