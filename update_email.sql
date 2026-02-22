-- ─────────────────────────────────────────────────────────────
-- Crop Estimator — Database Schema
-- ─────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS crop_system;
USE crop_system;

-- ─────────────────────────────────────────────────────────────
-- Users Table
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100)        NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    password    VARCHAR(255)        NOT NULL,   -- bcrypt hash
    is_admin    TINYINT(1)          DEFAULT 0,
    created_at  DATETIME            DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────────
-- Predictions Table
-- Stores inputs + all 8 model outputs + majority recommendation
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT         NOT NULL,

    -- Soil inputs
    nitrogen        FLOAT       NOT NULL,
    phosphorus      FLOAT       NOT NULL,
    potassium       FLOAT       NOT NULL,
    temperature     FLOAT       NOT NULL,
    humidity        FLOAT       NOT NULL,
    ph              FLOAT       NOT NULL,
    rainfall        FLOAT       NOT NULL,

    -- Final recommendation (majority vote, tie-broken by best model)
    predicted_crop  VARCHAR(50) NOT NULL,

    -- Individual model predictions
    rf_crop         VARCHAR(50),   -- Random Forest
    dt_crop         VARCHAR(50),   -- Decision Tree
    svm_crop        VARCHAR(50),   -- SVM
    lr_crop         VARCHAR(50),   -- Logistic Regression
    knn_crop        VARCHAR(50),   -- KNN
    nb_crop         VARCHAR(50),   -- Naive Bayes
    gb_crop         VARCHAR(50),   -- Gradient Boost
    ada_crop        VARCHAR(50),   -- AdaBoost

    -- Best accuracy model name
    best_model      VARCHAR(50),

    created_at      DATETIME    DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Password Reset Tokens Table
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT         NOT NULL,
    token       VARCHAR(255) UNIQUE NOT NULL,
    expires_at  DATETIME    NOT NULL,
    used        TINYINT(1)  DEFAULT 0,
    created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);