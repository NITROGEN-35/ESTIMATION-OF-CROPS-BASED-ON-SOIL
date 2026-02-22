from flask import Blueprint, jsonify, session
from db import get_db_connection

admin_bp = Blueprint("admin", __name__)

def require_admin():
    if "user_id" not in session or not session.get("is_admin"):
        return False
    return True


@admin_bp.route("/admin")
def admin_home():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"message": "Admin panel"})


@admin_bp.route("/admin/users")
def users():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, email, created_at FROM users")
    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)


@admin_bp.route("/admin/predictions")
def predictions():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM predictions")
    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)
