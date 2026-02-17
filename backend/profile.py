from flask import Blueprint, request, jsonify
from db import get_db_connection

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["POST"])
def update_profile():
    uid = request.headers.get("X-User-Id")
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET full_name=%s, email=%s WHERE id=%s",
        (data["full_name"], data["email"], uid)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "updated"})
