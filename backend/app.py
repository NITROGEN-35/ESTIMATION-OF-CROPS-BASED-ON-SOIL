from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pandas as pd

from ml_core import predict_crop
from db import get_db_connection
from auth import auth_bp
from admin import admin_bp
from profile import profile_bp

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY"
CORS(app, supports_credentials=True)


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(profile_bp)


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return jsonify({"message": "API running ✅"})


# -------------------------
# DASHBOARD (AUTH REQUIRED)
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"message": "Dashboard loaded"})


# -------------------------
# HISTORY
# -------------------------
@app.route("/history")
def history():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM predictions WHERE user_id=%s",
        (session["user_id"],)
    )

    data = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(data)


# -------------------------
# PREDICT (AUTH REQUIRED)
# -------------------------
@app.route("/predict", methods=["POST"])
def predict():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    df = pd.DataFrame([[data[k] for k in [
        "N","P","K","temperature","humidity","ph","rainfall"
    ]]], columns=[
        "N","P","K","temperature","humidity","ph","rainfall"
    ])

    preds, accs, best = predict_crop(df)

    # SAVE TO DATABASE
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO predictions 
        (user_id, nitrogen, phosphorus, potassium,
         temperature, humidity, ph, rainfall, predicted_crop)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        session["user_id"],
        data["N"], data["P"], data["K"],
        data["temperature"], data["humidity"],
        data["ph"], data["rainfall"],
        preds[best]
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "predictions": preds,
        "accuracies": accs,
        "best_model": best,
        "recommended_crop": preds[best]
    })


if __name__ == "__main__":
    app.run(debug=True)
