"""
rf_model.py

This script handles the creation, training, evaluation, and feature importance analysis
of Random Forest models for migraine prediction using combined migraine and weather data.

Workflow:
- Loads and processes data using functions from data_processing.py.
- Performs feature engineering and prepares data for modeling.
- Trains and evaluates a Random Forest model for binary classification (migraine occurrence).
- Trains and evaluates a Random Forest model for regression (pain level, log-transformed).
- Saves the trained classification model.
- Outputs evaluation metrics and feature importances for both tasks.
"""

from data_processing import merge_migraine_and_weather_data, process_combined_data
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error, mean_squared_error
import pandas as pd
import numpy as np
import os

model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'rf_model.pkl')

# Prepare data
merge_migraine_and_weather_data()
combined_data = process_combined_data()

# Prepare features and target variable
features = combined_data.drop(columns=[
    'Date', 'date', 
    'Medication', 
    'Dosage', 
    'Triggers',
    'Notes', 
    'Location', 
    'Timezone', 
    'Pain Level',
    'Pain_Level_Binary',
    'Longitude_x',
    'Latitude_x',
    'Longitude_y',
    'Latitude_y',
    'Time',
    ])  # Drop non-feature columns
target_binary = combined_data['Pain_Level_Binary']

# Split data into training and testing sets for binary classification
X_train_bin, X_test_bin, y_train_bin, y_test_bin = train_test_split(features, target_binary, test_size=0.2, random_state=42)

# Train a machine learning model
clf = RandomForestRegressor()
clf.fit(X_train_bin, y_train_bin)

import joblib
# Save the trained model
joblib.dump(clf, model_path)

# Make predictions
y_pred_bin = clf.predict(X_test_bin)

# Ensure the predictions are binary
y_pred_bin = (y_pred_bin > 0.5).astype(int)

# Evaluate the binary classification model
accuracy = accuracy_score(y_test_bin, y_pred_bin)
f1 = f1_score(y_test_bin, y_pred_bin)

print(f"Binary Classification Accuracy: {accuracy}")
print(f"Binary Classification F1 Score: {f1}")

# Prepare features and target variable for regression (non-zero cases)
non_zero_data = combined_data[combined_data['Pain Level'] > 0]
features_non_zero = non_zero_data.drop(columns=[
    'Date', 'date', 
    'Medication', 
    'Dosage', 
    'Triggers',
    'Notes', 
    'Location', 
    'Timezone', 
    'Pain Level',
    'Pain_Level_Binary',
    'Pain_Level_Log',
    'Longitude_x',
    'Latitude_x',
    'Longitude_y',
    'Latitude_y',
    'Time'
])  # Drop non-feature columns
target_non_zero = non_zero_data['Pain_Level_Log']

# Split data into training and testing sets for regression
X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(features_non_zero, target_non_zero, test_size=0.2, random_state=42)

# Train a regression model
best_params = {'bootstrap': True, 'max_depth': 30, 'min_samples_leaf': 1, 'min_samples_split': 2, 'n_estimators': 200}
reg = RandomForestRegressor(**best_params)
reg.fit(X_train_reg, y_train_reg)

# Make predictions for regression
y_pred_reg = reg.predict(X_test_reg)

# Evaluate the regression model
r2 = r2_score(y_test_reg, y_pred_reg)
mae = mean_absolute_error(y_test_reg, y_pred_reg)
mse = mean_squared_error(y_test_reg, y_pred_reg)
rmse = np.sqrt(mse)

print(f"Regression Model R^2 score: {r2}")
print(f"Mean Absolute Error (MAE): {mae}")
print(f"Mean Squared Error (MSE): {mse}")
print(f"Root Mean Squared Error (RMSE): {rmse}")

# Calculate feature importance for regression model
feature_importances = reg.feature_importances_
feature_names = features_non_zero.columns
importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': feature_importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False)

print("Feature importances for regression model:")
print(importance_df)