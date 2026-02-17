from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

from ml_core import predict_crop
from db import get_db_connection
from auth import auth_bp
from admin import admin_bp
from profile import profile_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(profile_bp)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    df = pd.DataFrame([[data[k] for k in [
        "N","P","K","temperature","humidity","ph","rainfall"
    ]]], columns=[
        "N","P","K","temperature","humidity","ph","rainfall"
    ])

    preds, accs, best = predict_crop(df)

    return jsonify({
        "predictions": preds,
        "accuracies": accs,
        "best_model": best,
        "recommended_crop": preds[best]
    })

@app.route("/")
def home():
    return "API running ✅"

if __name__ == "__main__":
    app.run(debug=True)
