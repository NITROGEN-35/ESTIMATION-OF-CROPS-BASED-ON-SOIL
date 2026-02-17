from flask import Blueprint, request, jsonify
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, is_admin FROM users WHERE email=%s AND password_hash=%s",
        (data["email"], data["password"])
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "user_id": user["id"],
        "is_admin": user["is_admin"]
    })
