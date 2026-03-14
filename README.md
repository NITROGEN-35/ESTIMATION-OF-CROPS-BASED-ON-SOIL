# 🌱 Estimation of Crops Based on Soil Parameters

> A machine learning web application that recommends the most suitable crop to grow based on soil nutrient values, climate parameters, and environmental conditions.

---

## 📌 Project Overview

This project uses **8 machine learning classification models** to predict the best crop for a given set of soil and climate inputs. The system compares all model predictions, shows accuracy metrics, and recommends the crop suggested by the highest-accuracy model.

Built as a research and practical agriculture tool, it features a clean dashboard UI, prediction history, model comparison charts, and input validation with threshold warnings.

---

## 🖥️ Screenshots

| Landing Page                        | Dashboard                               | Prediction Results                  |
| ----------------------------------- | --------------------------------------- | ----------------------------------- |
| ![Landing](screenshots/landing.png) | ![Dashboard](screenshots/dashboard.png) | ![Results](screenshots/results.png) |

> _(Add your own screenshots to a `/screenshots` folder in the repo)_

---

## 🧰 Tech Stack

| Layer                | Technology                        |
| -------------------- | --------------------------------- |
| **Frontend**         | HTML5, CSS3, JavaScript (Vanilla) |
| **Charts**           | Chart.js                          |
| **Backend**          | Python, Flask, Flask-CORS         |
| **Machine Learning** | scikit-learn                      |
| **Database**         | MySQL (crop_system.sql)           |
| **Icons**            | Font Awesome, Boxicons            |
| **Fonts**            | Google Fonts (Inter)              |

---

## 🤖 Machine Learning Models Used

| Model                        | Description                                             |
| ---------------------------- | ------------------------------------------------------- |
| Random Forest                | Ensemble of decision trees — typically highest accuracy |
| Decision Tree                | Single tree, fast and interpretable                     |
| Support Vector Machine (SVM) | Finds optimal hyperplane boundary                       |
| Logistic Regression          | Probabilistic linear classifier                         |
| Naive Bayes                  | Probabilistic model using Bayes' theorem                |
| K-Nearest Neighbors (KNN)    | Classifies based on closest training samples            |
| Gradient Boosting            | Sequential boosting for high accuracy                   |
| AdaBoost                     | Adaptive boosting — reduces bias iteratively            |

All models are trained on an 80/20 train-test split with **StandardScaler** normalization.

---

## 📊 Dataset

**File:** `Crop_recommendation.csv`

**Source:** [Kaggle — Crop Recommendation Dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)

### Features (Input Columns)

| Feature       | Unit  | Description                |
| ------------- | ----- | -------------------------- |
| `N`           | kg/ha | Nitrogen content in soil   |
| `P`           | kg/ha | Phosphorus content in soil |
| `K`           | kg/ha | Potassium content in soil  |
| `temperature` | °C    | Average temperature        |
| `humidity`    | %     | Relative humidity          |
| `ph`          | —     | Soil pH value              |
| `rainfall`    | mm    | Annual rainfall            |

### Target Column

| Column  | Type   | Description                                         |
| ------- | ------ | --------------------------------------------------- |
| `label` | string | Crop name (22 classes: rice, maize, chickpea, etc.) |

### Dataset Statistics

- **Rows:** 2,200 samples
- **Classes:** 22 crop types
- **Balance:** 100 samples per crop (balanced dataset)

---

## 🏗️ System Architecture

```
User Browser
     │
     ▼
 dashboard.html  ──── style.css
     │
     ├── script.js   (form, validation, localStorage history)
     └── chart.js    (Chart.js rendering, fetch to backend)
          │
          ▼
   Flask API (app.py)  :5000
          │
          ├── /predict   POST  → returns predictions + accuracies
          └── /          GET   → health check
               │
               ▼
    scikit-learn Models
    (Random Forest, SVM, etc.)
               │
               ▼
    Crop_recommendation.csv
```

---

## ✅ Input Validation System

The app enforces **two-layer validation**:

### Layer 1 — Frontend (script.js)

Hard stops the request if values are outside absolute dataset bounds:

| Parameter   | Min | Max |
| ----------- | --- | --- |
| N           | 0   | 140 |
| P           | 0   | 145 |
| K           | 0   | 205 |
| Temperature | 5   | 45  |
| Humidity    | 20  | 100 |
| pH          | 3.5 | 9.0 |
| Rainfall    | 20  | 300 |

### Layer 2 — Backend (app.py)

Warns if values are outside the comfortable agronomic range and applies a confidence penalty:

| Parameter   | Min | Max |
| ----------- | --- | --- |
| N           | 15  | 150 |
| P           | 30  | 80  |
| K           | 15  | 120 |
| Temperature | 10  | 35  |
| Humidity    | 30  | 90  |
| pH          | 5.0 | 8.0 |
| Rainfall    | 20  | 300 |

---

## 🔌 API Reference

### `POST /predict`

**Request Body (JSON):**

```json
{
  "N": 90,
  "P": 42,
  "K": 43,
  "temperature": 20.8,
  "humidity": 82.0,
  "ph": 6.5,
  "rainfall": 202.9
}
```

**Response (JSON):**

```json
{
  "predictions": {
    "random_forest": "rice",
    "decision_tree": "rice",
    "svm": "rice",
    "logistic_regression": "rice",
    "naive_bayes": "rice",
    "knn": "rice",
    "gradient_boost": "rice",
    "adaboost": "rice"
  },
  "accuracies": {
    "random_forest": 99.32,
    "decision_tree": 98.18,
    ...
  },
  "best_model": "random_forest",
  "recommended_crop": "rice",
  "threshold_status": "ok",
  "threshold_warnings": [],
  "confidence_penalty": 0
}
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- MySQL (optional, for persistent history)
- A modern web browser

### 1. Clone the Repository

```bash
git clone https://github.com/NITROGEN-35/ESTIMATION-OF-CROPS-BASED-ON-SOIL.git
cd ESTIMATION-OF-CROPS-BASED-ON-SOIL
```

### 2. Install Python Dependencies

```bash
pip install flask flask-cors scikit-learn pandas numpy
```

### 3. Add the Dataset

Place `Crop_recommendation.csv` in the project root directory.
Download from: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset

### 4. Start the Backend

```bash
python app.py
```

Or on Windows:

```bash
start_backend.bat
```

The Flask server will start at: `http://127.0.0.1:5000`

### 5. Open the Frontend

Open `dashboard.html` directly in your browser, or serve via Live Server (VS Code extension).

### 6. (Optional) Set Up MySQL Database

```bash
mysql -u root -p < crop_system.sql
```

---

## 📁 Project Structure

```
ESTIMATION-OF-CROPS-BASED-ON-SOIL/
│
├── app.py                   # Flask backend + ML models
├── dashboard.html           # Main prediction dashboard
├── history.html             # Prediction history page
├── indexl.html              # Landing page
├── script.js                # Form handling, validation, history
├── chart.js                 # Chart rendering, API calls
├── style.css                # All styling
├── crop_system.sql          # MySQL schema
├── start_backend.bat        # Windows batch launcher
├── Crop_recommendation.csv  # Dataset (add manually)
└── README.md
```

---

## 📈 Model Performance (Typical)

| Model               | Accuracy |
| ------------------- | -------- |
| Random Forest       | ~99%     |
| Gradient Boosting   | ~98%     |
| Decision Tree       | ~98%     |
| SVM                 | ~97%     |
| KNN                 | ~97%     |
| Naive Bayes         | ~99%     |
| Logistic Regression | ~95%     |
| AdaBoost            | ~93%     |

_Exact values depend on the random state and train/test split._

---

## 🌾 Supported Crops (22 Classes)

`rice` · `maize` · `chickpea` · `kidneybeans` · `pigeonpeas` · `mothbeans` · `mungbean` · `blackgram` · `lentil` · `pomegranate` · `banana` · `mango` · `grapes` · `watermelon` · `muskmelon` · `apple` · `orange` · `papaya` · `coconut` · `cotton` · `jute` · `coffee`

---

## 🔒 Security Notes

- Frontend input validation blocks requests outside dataset bounds
- Backend threshold validation adds a confidence penalty for edge-case inputs
- No sensitive credentials are hardcoded in source files
- MySQL passwords should be stored in environment variables in production

---

## 🙋 Author

**Sanyam Kushwaha**
GitHub: [@NITROGEN-35](https://github.com/NITROGEN-35)

---

## 📄 License

This project is for academic and research purposes.

---

## 🏷️ Tags

`machine-learning` `crop-recommendation` `agriculture` `flask` `scikit-learn` `random-forest` `soil-analysis` `python` `javascript` `chart.js`
