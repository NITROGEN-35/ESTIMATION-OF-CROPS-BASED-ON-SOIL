import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report
from collections import Counter
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Crop_recommendation.csv")

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    raise RuntimeError(f"Dataset not found at {CSV_PATH}.")

X = df.drop('label', axis=1)
y = df['label']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

models = {
    "random_forest":        RandomForestClassifier(random_state=42),
    "decision_tree":        DecisionTreeClassifier(random_state=42),
    "svm":                  SVC(random_state=42),
    "logistic_regression":  LogisticRegression(max_iter=1000, random_state=42),
    "naive_bayes":          GaussianNB(),
    "knn":                  KNeighborsClassifier(),
    "gradient_boost":       GradientBoostingClassifier(random_state=42),
    "adaboost":             AdaBoostClassifier(random_state=42),
}

for model in models.values():
    model.fit(X_train_scaled, y_train)

# Precompute all metrics at startup
def _compute_metrics(name, model):
    y_pred = model.predict(X_test_scaled)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    return {
        "accuracy":  round(accuracy_score(y_test, y_pred) * 100, 2),
        "precision": round(report["weighted avg"]["precision"] * 100, 2),
        "recall":    round(report["weighted avg"]["recall"] * 100, 2),
        "f1":        round(report["weighted avg"]["f1-score"] * 100, 2),
    }

model_metrics = {name: _compute_metrics(name, model) for name, model in models.items()}
accuracies = {name: model_metrics[name]["accuracy"] for name in models}


def predict_crop(input_df):
    scaled = scaler.transform(input_df)
    preds = {name: model.predict(scaled)[0] for name, model in models.items()}
    vote_counts = Counter(preds.values())
    max_votes = max(vote_counts.values())
    top_crops = [crop for crop, count in vote_counts.items() if count == max_votes]
    best_model = max(accuracies, key=accuracies.get)
    recommended_crop = top_crops[0] if len(top_crops) == 1 else preds[best_model]
    return preds, accuracies, best_model, recommended_crop, dict(vote_counts)
