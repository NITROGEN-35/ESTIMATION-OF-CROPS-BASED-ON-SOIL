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

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "Crop_recommendation.csv")

df = pd.read_csv(CSV_PATH)


X = df.drop('label', axis=1)
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

models = {
    "random_forest": RandomForestClassifier(),
    "decision_tree": DecisionTreeClassifier(),
    "svm": SVC(),
    "logistic_regression": LogisticRegression(max_iter=1000),
    "naive_bayes": GaussianNB(),
    "knn": KNeighborsClassifier(),
    "gradient_boost": GradientBoostingClassifier(),
    "adaboost": AdaBoostClassifier()
}

for m in models.values():
    m.fit(X_train_scaled, y_train)

accuracies = {
    name: round(accuracy_score(y_test, model.predict(X_test_scaled)) * 100, 2)
    for name, model in models.items()
}

def predict_crop(input_df):
    scaled = scaler.transform(input_df)
    preds = {k: m.predict(scaled)[0] for k, m in models.items()}
    best_model = max(accuracies, key=accuracies.get)
    return preds, accuracies, best_model
