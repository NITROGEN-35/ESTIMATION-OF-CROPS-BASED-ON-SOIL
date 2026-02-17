from flask import Blueprint, request, jsonify
from db import get_db_connection

admin_bp = Blueprint("admin", __name__)

def require_admin():
    uid = request.headers.get("X-User-Id")
    if not uid:
        return None
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT is_admin FROM users WHERE id=%s", (uid,))
    u = cur.fetchone()
    cur.close()
    conn.close()
    return u if u and u["is_admin"] == 1 else None

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
