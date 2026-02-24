import os
from pathlib import Path
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Auto-load .env from backend/ directory ─────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

from ml_core import predict_crop
from db import get_db_connection
from auth import auth_bp, get_current_user
from admin import admin_bp
from profile import profile_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(profile_bp)


# ===============================
# Soil Health Score Function
# ===============================
def calculate_soil_score(N, P, K, temperature, humidity, ph, rainfall):
    score = 0

    # pH (25)
    if 6.0 <= ph <= 7.5:
        score += 25
    elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
        score += 18
    elif 5.0 <= ph < 5.5 or 8.0 < ph <= 8.5:
        score += 10
    else:
        score += 5

    # NPK (35)
    npk_score = 35
    for value in [N, P, K]:
        if value < 30:
            npk_score -= 8
        elif value > 150:
            npk_score -= 5
    score += max(npk_score, 0)

    # Moisture (20)
    if 40 <= humidity <= 80 and 50 <= rainfall <= 300:
        score += 20
    else:
        score += 10

    # Temperature (20)
    if 20 <= temperature <= 30:
        score += 20
    elif 30 < temperature <= 35:
        score += 10
    else:
        score += 5

    # ensure float for consistency (could be int when score is a round
    # number, which broke one of the white‑box tests).
    return float(round(score, 2))


# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({"message": "Crop Estimator API running ✅"})


# ─────────────────────────────────────────────
# HISTORY  (JWT-protected)
# ─────────────────────────────────────────────
@app.route("/history/<int:user_id>")
def history(user_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user["user_id"] != user_id:
        return jsonify({"error": "Forbidden"}), 403

    try:
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM predictions WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        data = cur.fetchall()
        cur.close()
        conn.close()
        # Convert datetime objects to ISO strings for JSON serialisation
        for row in data:
            if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
                row["created_at"] = row["created_at"].isoformat()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# ─────────────────────────────────────────────
# PREDICT  (JWT-protected)
# ─────────────────────────────────────────────
REQUIRED_FIELDS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

@app.route("/predict", methods=["POST"])
def predict():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # `get_json(force=True)` will return `{}` for an empty object, but
        # `None` when the body isn't valid JSON at all.  Treat only the latter
        # as "no JSON received" so that an empty dict triggers the regular
        # missing‑fields message.
        data = request.get_json(force=True)
        if data is None:
            return jsonify({"error": "No JSON body received"}), 400

        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        try:
            values = [float(data[f]) for f in REQUIRED_FIELDS]
        except (ValueError, TypeError):
            return jsonify({"error": "All inputs must be numeric"}), 400

        N, P, K, temperature, humidity, ph, rainfall = values

        errors = []
        if not (0 <= N <= 200):            errors.append("N must be 0–200")
        if not (0 <= P <= 200):            errors.append("P must be 0–200")
        if not (0 <= K <= 200):            errors.append("K must be 0–200")
        if not (-20 <= temperature <= 60): errors.append("Temperature must be -20 to 60°C")
        if not (0 <= humidity <= 100):     errors.append("Humidity must be 0–100%")
        if not (0 <= ph <= 14):            errors.append("pH must be 0–14")
        if not (0 <= rainfall <= 500):     errors.append("Rainfall must be 0–500 mm")
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        input_df = pd.DataFrame([values], columns=REQUIRED_FIELDS)
        preds, accs, best_model, recommended_crop, votes = predict_crop(input_df)

        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO predictions (
                    user_id, nitrogen, phosphorus, potassium,
                    temperature, humidity, ph, rainfall,
                    predicted_crop,
                    rf_crop, dt_crop, svm_crop,
                    lr_crop, knn_crop, nb_crop,
                    gb_crop, ada_crop, best_model
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                user["user_id"],
                N, P, K, temperature, humidity, ph, rainfall,
                recommended_crop,
                preds.get("random_forest"),     preds.get("decision_tree"),
                preds.get("svm"),               preds.get("logistic_regression"),
                preds.get("knn"),               preds.get("naive_bayes"),
                preds.get("gradient_boost"),    preds.get("adaboost"),
                best_model,
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_err:
            return jsonify({"error": f"Database error: {str(db_err)}"}), 500

        return jsonify({
            "predictions":      preds,
            "accuracies":       accs,
            "votes":            votes,
            "best_model":       best_model,
            "recommended_crop": recommended_crop,
        })

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)