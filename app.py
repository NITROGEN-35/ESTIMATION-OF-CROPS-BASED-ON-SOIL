import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import mysql.connector


def require_admin():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None, jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, is_admin FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user or user["is_admin"] != 1:
            return None, jsonify({"error": "Forbidden"}), 403

        return user, None, None

    except Exception:
        return None, jsonify({"error": "Server error"}), 500




def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="NITROGEN35",      # XAMPP default
        database="crop_system"
    )

# ---------------- Flask App ----------------
app = Flask(__name__)
CORS(app)

# ---------------- Load Dataset ----------------
df = pd.read_csv("Crop_recommendation.csv")

X = df.drop('label', axis=1)
y = df['label']

# ---------------- Train-Test Split ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------------- Scaling ----------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ---------------- Models ----------------
rf_model = RandomForestClassifier()
dt_model = DecisionTreeClassifier()
svm_model = SVC()
lr_model = LogisticRegression(max_iter=1000)
nb_model = GaussianNB()
knn_model = KNeighborsClassifier()
gb_model = GradientBoostingClassifier()
ada_model = AdaBoostClassifier()

models = {
    "random_forest": rf_model,
    "decision_tree": dt_model,
    "svm": svm_model,
    "logistic_regression": lr_model,
    "naive_bayes": nb_model,
    "knn": knn_model,
    "gradient_boost": gb_model,
    "adaboost": ada_model
}

# ---------------- Train Models ----------------
for model in models.values():
    model.fit(X_train_scaled, y_train)

# ---------------- Accuracy Calculation ----------------
accuracies = {
    name: round(accuracy_score(y_test, model.predict(X_test_scaled)) * 100, 2)
    for name, model in models.items()
}

print("[MODEL ACCURACIES]")
for k, v in accuracies.items():
    print(k, ":", v)

# ================== GLOBAL THRESHOLD LIMITS ==================
GLOBAL_THRESHOLDS = {
    "N": {"min": 15, "max": 150},          # kg/ha
    "P": {"min": 30, "max": 80},           # kg/ha
    "K": {"min": 15, "max": 120},          # kg/ha
    "temperature": {"min": 10, "max": 35}, # °C (comfort zone)
    "humidity": {"min": 30, "max": 90},    # %
    "ph": {"min": 5.0, "max": 8.0},        # pH scale
    "rainfall": {"min": 20, "max": 300}    # mm
}

def validate_global_thresholds(input_data):
    """
    Validates input values against global threshold limits.
    Returns:
        is_valid (bool)
        warnings (list of strings)
    """
    warnings = []

    for key, limits in GLOBAL_THRESHOLDS.items():
        value = input_data.get(key)

        if value is None:
            continue  # missing already handled elsewhere

        if value < limits["min"] or value > limits["max"]:
            warnings.append(
                f"{key} value {value} is outside recommended range "
                f"({limits['min']} – {limits['max']})"
            )

    return len(warnings) == 0, warnings



# ---------------- Prediction Endpoint ----------------
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json or {}

    required = ['N','P','K','temperature','humidity','ph','rainfall']
    for r in required:
        if r not in data:
            return jsonify({"error": f"Missing field: {r}"}), 400

    # ---------- Threshold validation ----------
    is_valid, threshold_warnings = validate_global_thresholds(data)

    input_df = pd.DataFrame([[
        float(data['N']),
        float(data['P']),
        float(data['K']),
        float(data['temperature']),
        float(data['humidity']),
        float(data['ph']),
        float(data['rainfall'])
    ]], columns=X.columns)

    input_scaled = scaler.transform(input_df)

    predictions = {
        name: model.predict(input_scaled)[0]
        for name, model in models.items()
    }

    best_model = max(accuracies, key=accuracies.get)

    confidence_penalty = 0
    if not is_valid:
        confidence_penalty = min(len(threshold_warnings) * 5, 20)

    # -------- Save prediction history (MINIMAL) --------
    user_id = request.headers.get("X-User-Id")

    if user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO predictions (
                    user_id,
                    nitrogen, phosphorus, potassium,
                    temperature, humidity, ph, rainfall,
                    predicted_crop, best_model
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                int(user_id),
                data['N'], data['P'], data['K'],
                data['temperature'], data['humidity'],
                data['ph'], data['rainfall'],
                predictions[best_model],
                best_model
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            print("History save failed:", e)

    return jsonify({
        "predictions": predictions,
        "accuracies": accuracies,
        "best_model": best_model,
        "recommended_crop": predictions[best_model],
        "threshold_status": "ok" if is_valid else "warning",
        "threshold_warnings": threshold_warnings,
        "confidence_penalty": confidence_penalty
    })

    
@app.route('/history', methods=['GET'])
def get_history():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                nitrogen, phosphorus, potassium,
                temperature, humidity, ph, rainfall,
                predicted_crop, best_model, created_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(records), 200

    except Exception as e:
        print("History fetch failed:", e)
        return jsonify({"error": "Failed to fetch history"}), 500

@app.route('/admin/users', methods=['GET'])
def admin_list_users():
    user, error, status = require_admin()
    if error:
        return error, status

    page = max(int(request.args.get("page", 1)), 1)
    perpage = min(int(request.args.get("perpage", 20)), 50)
    offset = (page - 1) * perpage

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, full_name, email, is_admin, created_at
        FROM users
        LIMIT %s OFFSET %s
    """, (perpage, offset))

    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(users), 200

@app.route('/admin/history', methods=['GET'])
def admin_history():
    user, error, status = require_admin()
    if error:
        return error, status

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT user_id, predicted_crop, best_model, created_at
        FROM predictions
        ORDER BY created_at DESC
        LIMIT 20
    """)

    history = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(history), 200




# ---------------- Home ----------------
@app.route('/')
def home():
    return "Crop Prediction Research API is running ✅"

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
