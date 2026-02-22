from flask import Blueprint, request, jsonify
from db import get_db_connection
from auth import get_current_user

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/update_profile", methods=["POST"])
def update_profile():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data      = request.get_json(force=True) or {}
    full_name = data.get("full_name", "").strip()
    email     = data.get("email", "").strip().lower()

    if not full_name or not email:
        return jsonify({"error": "full_name and email are required"}), 400

    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE users SET full_name=%s, email=%s WHERE id=%s",
            (full_name, email, user["user_id"])
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500