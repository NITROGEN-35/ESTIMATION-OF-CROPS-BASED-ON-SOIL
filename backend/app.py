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
# Note: SVC needs probability=True for confidence scores
rf_model  = RandomForestClassifier(random_state=42)
dt_model  = DecisionTreeClassifier(random_state=42)
svm_model = SVC(probability=True, random_state=42)   # ← probability=True
lr_model  = LogisticRegression(max_iter=1000, random_state=42)
nb_model  = GaussianNB()
knn_model = KNeighborsClassifier()
gb_model  = GradientBoostingClassifier(random_state=42)
ada_model = AdaBoostClassifier(random_state=42)

models = {
    "random_forest":      rf_model,
    "decision_tree":      dt_model,
    "svm":                svm_model,
    "logistic_regression": lr_model,
    "naive_bayes":        nb_model,
    "knn":                knn_model,
    "gradient_boost":     gb_model,
    "adaboost":           ada_model
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
    print(f"  {k}: {v}%")

# ================== GLOBAL THRESHOLD LIMITS ==================
GLOBAL_THRESHOLDS = {
    "N":           {"min": 15,  "max": 150},   # kg/ha
    "P":           {"min": 30,  "max": 80},    # kg/ha
    "K":           {"min": 15,  "max": 120},   # kg/ha
    "temperature": {"min": 10,  "max": 35},    # °C
    "humidity":    {"min": 30,  "max": 90},    # %
    "ph":          {"min": 5.0, "max": 8.0},   # pH
    "rainfall":    {"min": 20,  "max": 300}    # mm
}

def validate_global_thresholds(input_data):
    """
    Validates input values against global agronomic threshold limits.
    Returns:
        is_valid  (bool)
        warnings  (list of strings)
    """
    warnings = []
    for key, limits in GLOBAL_THRESHOLDS.items():
        value = input_data.get(key)
        if value is None:
            continue
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

    # --- Required fields check ---
    required = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    for r in required:
        if r not in data:
            return jsonify({"error": f"Missing field: {r}"}), 400

    # --- Threshold validation ---
    is_valid, threshold_warnings = validate_global_thresholds(data)

    # --- Build input DataFrame ---
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

    # --- Hard predictions (all models) ---
    predictions = {
        name: model.predict(input_scaled)[0]
        for name, model in models.items()
    }

    # --- Confidence scores (probability of predicted class, all models) ---
    confidence_scores = {}
    for name, model in models.items():
        if hasattr(model, "predict_proba"):
            proba_array = model.predict_proba(input_scaled)[0]
            classes     = list(model.classes_)
            pred_class  = predictions[name]
            if pred_class in classes:
                idx = classes.index(pred_class)
                confidence_scores[name] = round(float(proba_array[idx]) * 100, 2)
            else:
                confidence_scores[name] = None
        else:
            confidence_scores[name] = None

    # --- Best model (by test accuracy) ---
    best_model = max(accuracies, key=accuracies.get)

    # --- Confidence penalty for out-of-range inputs ---
    confidence_penalty = 0
    if not is_valid:
        confidence_penalty = min(len(threshold_warnings) * 5, 20)

    # --- Top-3 crop probabilities from Random Forest ---
    rf_proba  = rf_model.predict_proba(input_scaled)[0]
    rf_classes = list(rf_model.classes_)
    top3_idx  = rf_proba.argsort()[-3:][::-1]
    top3_crops = [
        {"crop": rf_classes[i], "probability": round(float(rf_proba[i]) * 100, 2)}
        for i in top3_idx
    ]

    return jsonify({
        "predictions":         predictions,
        "accuracies":          accuracies,
        "best_model":          best_model,
        "recommended_crop":    predictions[best_model],

        # ✅ NEW: per-model confidence scores
        "confidence_scores":   confidence_scores,

        # ✅ NEW: top 3 crop alternatives from Random Forest
        "top3_crops":          top3_crops,

        # Threshold feedback
        "threshold_status":    "ok" if is_valid else "warning",
        "threshold_warnings":  threshold_warnings,
        "confidence_penalty":  confidence_penalty
    })


# ---------------- Health Check ----------------
@app.route('/')
def home():
    return "Crop Prediction API is running ✅"


# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)