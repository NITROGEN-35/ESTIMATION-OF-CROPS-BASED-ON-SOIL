from flask import Blueprint, jsonify
from db import get_db_connection
from auth import require_admin

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
def admin_home():
    if not require_admin():
        return jsonify({"error": "Forbidden – admin only"}), 403
    return jsonify({"message": "Admin panel active"})


@admin_bp.route("/admin/users")
def users():
    if not require_admin():
        return jsonify({"error": "Forbidden – admin only"}), 403
    try:
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id, full_name, email, is_admin, created_at FROM users ORDER BY created_at DESC")
        data = cur.fetchall()
        cur.close()
        conn.close()
        for row in data:
            if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
                row["created_at"] = row["created_at"].isoformat()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@admin_bp.route("/admin/predictions")
def predictions():
    if not require_admin():
        return jsonify({"error": "Forbidden – admin only"}), 403
    try:
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM predictions ORDER BY created_at DESC")
        data = cur.fetchall()
        cur.close()
        conn.close()
        for row in data:
            if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
                row["created_at"] = row["created_at"].isoformat()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500