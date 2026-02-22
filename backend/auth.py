from flask import Blueprint, request, jsonify, session
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)

# -------------------------
# LOGIN
# -------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT id, is_admin FROM users WHERE email=%s AND password_hash=%s",
        (data["email"], data["password"])
    )

    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user["id"]
    session["is_admin"] = user["is_admin"]

    return jsonify({
        "user_id": user["id"],
        "is_admin": user["is_admin"]
    })


# -------------------------
# LOGOUT
# -------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return jsonify({"status": "logged out"})
