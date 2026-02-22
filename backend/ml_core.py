import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from collections import Counter
import os

# ─────────────────────────────────────────────
# Dataset Loading (with error handling)
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Crop_recommendation.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    raise RuntimeError(f"Dataset not found at {CSV_PATH}. Make sure Crop_recommendation.csv is in the project folder.")

# ─────────────────────────────────────────────
# Features & Labels
# ─────────────────────────────────────────────
X = df.drop('label', axis=1)
y = df['label']

# ─────────────────────────────────────────────
# Train / Test Split
# ─────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ─────────────────────────────────────────────
# Scaling — fitted ONCE on train only
# ─────────────────────────────────────────────
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ─────────────────────────────────────────────
# Models — trained ONCE at startup
# ─────────────────────────────────────────────
models = {
    "random_forest":      RandomForestClassifier(random_state=42),
    "decision_tree":      DecisionTreeClassifier(random_state=42),
    "svm":                SVC(random_state=42),
    "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
    "naive_bayes":        GaussianNB(),
    "knn":                KNeighborsClassifier(),
    "gradient_boost":     GradientBoostingClassifier(random_state=42),
    "adaboost":           AdaBoostClassifier(random_state=42),
}

for model in models.values():
    model.fit(X_train_scaled, y_train)

# ─────────────────────────────────────────────
# Accuracies — precomputed ONCE at startup
# ─────────────────────────────────────────────
accuracies = {
    name: round(accuracy_score(y_test, model.predict(X_test_scaled)) * 100, 2)
    for name, model in models.items()
}

# ─────────────────────────────────────────────
# Prediction Function
# ─────────────────────────────────────────────
def predict_crop(input_df):
    """
    Takes a 1-row DataFrame with columns:
        N, P, K, temperature, humidity, ph, rainfall

    Returns:
        preds           – dict of {model_name: crop}
        accuracies      – dict of {model_name: accuracy%}
        best_model      – name of highest-accuracy model
        recommended_crop – majority vote winner (tie broken by best model)
        vote_counts     – dict of {crop: vote_count}
    """
    scaled = scaler.transform(input_df)

    # All model predictions
    preds = {name: model.predict(scaled)[0] for name, model in models.items()}

    # Majority vote
    vote_counts = Counter(preds.values())
    max_votes   = max(vote_counts.values())
    top_crops   = [crop for crop, count in vote_counts.items() if count == max_votes]

    # Best accuracy model (used for tie-breaking)
    best_model = max(accuracies, key=accuracies.get)

    # Final recommendation:
    #   - If one clear majority winner → use that
    #   - If tie → defer to highest-accuracy model's prediction
    if len(top_crops) == 1:
        recommended_crop = top_crops[0]
    else:
        recommended_crop = preds[best_model]

    return preds, accuracies, best_model, recommended_crop, dict(vote_counts)