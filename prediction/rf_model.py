from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error, mean_squared_error
import pandas as pd
import numpy as np
import os

# Define the file paths using relative pathing
weather_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'weather_data.csv')
migraine_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'migraine_log.csv')
combined_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'combined_data.csv')
model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'rf_model.pkl')

# Merge migraine and weather data
def merge_migraine_and_weather_data(migraine_log_file=migraine_data_filename, weather_data_file=weather_data_filename, output_file=combined_data_filename):
    migraine_data = pd.read_csv(migraine_log_file)
    weather_data = pd.read_csv(weather_data_file)

    # Merge data on the 'Date' column
    combined_data = pd.merge(migraine_data, weather_data, left_on='Date', right_on='date', how='left')
    combined_data.to_csv(output_file, index=False)

merge_migraine_and_weather_data()

# Load combined data
combined_data = pd.read_csv(combined_data_filename)

# Convert 'Time' column to minutes since midnight
def convert_time_to_minutes(time_str):
    if pd.isna(time_str):
        return 0  # Default to midnight if time is missing
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

combined_data['Time'] = combined_data['Time'].apply(convert_time_to_minutes)

# Extract day of the week and month from 'Date' column
combined_data['Date'] = pd.to_datetime(combined_data['Date'])
combined_data['DayOfWeek'] = combined_data['Date'].dt.dayofweek
combined_data['Month'] = combined_data['Date'].dt.month
# One-hot encode 'DayOfWeek' and 'Month' columns
combined_data = pd.get_dummies(combined_data, columns=['DayOfWeek', 'Month'])

# One-hot encode 'Sleep' and 'Physical Activity' columns
combined_data = pd.get_dummies(combined_data, columns=['Sleep', 'Physical Activity'])

# Create new features
combined_data['tdiff'] = combined_data['tmax']-combined_data['tmin']
combined_data['tavg'] = (combined_data['tmax']+combined_data['tmin'])/2
# Create lag features for 'tavg'
combined_data['tavg_lag1'] = combined_data['tavg'].shift(1)
combined_data['tavg_lag2'] = combined_data['tavg'].shift(2)
# Create interaction term between 'average_humidity' and 'tavg'
combined_data['humid.*tavg'] = combined_data['average_humidity'] * combined_data['tavg']


# Clean 'Pain Level' column to ensure all values are numeric
combined_data['Pain Level'] = pd.to_numeric(combined_data['Pain Level'], errors='coerce').fillna(0)

# Apply logarithmic transformation to 'Pain Level'
combined_data['Pain Level'] = np.log1p(combined_data['Pain Level'])  # log1p is log(1 + x)

# Create a binary target variable for zero vs. non-zero 'Pain Level'
combined_data['Pain_Level_Binary'] = (combined_data['Pain Level'] > 0).astype(int)

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
    'Longitude_x',
    'Latitude_x',
    'Longitude_y',
    'Latitude_y',
    'Time'
])  # Drop non-feature columns
target_non_zero = np.log1p(non_zero_data['Pain Level'])  # Apply logarithmic transformation

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