"""
lstm_model.py

This script handles the creation, training, and evaluation of an LSTM model
for migraine pain level prediction using combined migraine and weather data.

Workflow:
- Loads and processes data using functions from data_processing.py.
- Prepares time-series data for LSTM input.
- Trains and evaluates an LSTM model for regression (pain level, log-transformed).
- Outputs evaluation metrics.
"""

from forecasting.data_loader import merge_migraine_and_weather_data, process_combined_data
import numpy as np
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

# Parameters
SEQ_LEN = 7  # Number of days in the input sequence
BATCH_SIZE = 32
EPOCHS = 50

# Prepare data
merge_migraine_and_weather_data()
combined_data = process_combined_data()

# Use only non-zero pain level data for regression
non_zero_data = combined_data[combined_data['Pain Level'] > 0].reset_index(drop=True)

# Drop non-feature columns
feature_cols = non_zero_data.drop(columns=[
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
]).columns

features = non_zero_data[feature_cols].values
target = non_zero_data['Pain_Level_Log'].values

# Prepare sequences for LSTM
def create_sequences(features, target, seq_len):
    X, y = [], []
    for i in range(len(features) - seq_len):
        X.append(features[i:i+seq_len])
        y.append(target[i+seq_len])
    return np.array(X), np.array(y)

X, y = create_sequences(features, target, SEQ_LEN)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build LSTM model
model = Sequential([
    LSTM(64, input_shape=(SEQ_LEN, X.shape[2]), return_sequences=False),
    Dense(32, activation='relu'),
    Dense(1)
])
model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

# Train model
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=[early_stop],
    verbose=1
)

# Evaluate model
y_pred = model.predict(X_test).flatten()
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)

print(f"LSTM Regression Model R^2 score: {r2}")
print(f"Mean Absolute Error (MAE): {mae}")
print(f"Mean Squared Error (MSE): {mse}")
print(f"Root Mean Squared Error (RMSE): {rmse}")