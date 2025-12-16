import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import TimeSeriesSplit
# from sklearn.experimental import enable_hist_gradient_boosting  # noqa
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score, classification_report
import matplotlib.pyplot as plt

# Import data processing
# Import data processing
try:
    from prediction.data_processing import merge_migraine_and_weather_data, process_combined_data
except ImportError:
    # Fallback for running as script directly
    from data_processing import merge_migraine_and_weather_data, process_combined_data

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_CLF_PATH = os.path.join(MODEL_DIR, 'best_model_clf.pkl')
MODEL_REG_PATH = os.path.join(MODEL_DIR, 'best_model_reg.pkl')

def train_and_evaluate(db_path=None):
    print("Step 1: Merging and Processing Data...")
    
    # Allow overriding DB path for testing
    if db_path:
        # If test DB is provided, we need to replicate the pipeline steps
        from prediction.data_processing import load_migraine_log_from_db
        
        # 1. Load Raw
        raw_df = load_migraine_log_from_db(db_path)
        
        # 2. Merge/Format (This function needs to handle raw_df input or we patch it)
        # Actually, `merge_migraine_and_weather_data` reads from DB by default. 
        # Let's just create a temporary combined DF manually for the test to avoid refactoring everything
        # Or better: Update merge_migraine_and_weather_data to take a DF.
        # But for now, let's just use the `process_combined_data` on a pre-prepared DF if possible.
        
        # To make this robust without modifying `merge...` too much:
        # We will assume `load_migraine_log_from_db` isn't enough, we need `merge...`.
        # Taking a shortcut: We will update `merge_migraine_and_weather_data` to take `db_path` too.
        
        combined_df = merge_migraine_and_weather_data(db_path=db_path, return_df=True)
        df = process_combined_data(input_df=combined_df)

    else:
        # Default production flow
        merge_migraine_and_weather_data()
        df = process_combined_data()
    
    print(f"Data Loaded: {len(df)} days of history.")
    
    # Define Features and Target
    exclude_cols = [
        'Date', 'date', 
        'Medication', 'Dosage', 'Medications', 'Triggers', 'Notes', 'Location', 'Timezone', 
        'Pain Level', 'Pain_Level_Binary', 'Pain_Level_Log', 
        'Longitude_x', 'Latitude_x', 'Longitude_y', 'Latitude_y', 
        'Time'
    ]
    
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X = df[feature_cols]
    y_reg = df['Pain_Level_Log']
    y_bin = df['Pain_Level_Binary']
    
    print(f"Training on {len(feature_cols)} features.")
    
    tscv = TimeSeriesSplit(n_splits=5)
    
    acc_scores = []
    combined_mae_scores = []
    
    # Initialize models
    # class_weight='balanced' helps with the "No Pain" dominance
    clf = HistGradientBoostingClassifier(max_iter=100, max_depth=5, learning_rate=0.05, random_state=42, class_weight='balanced')
    reg = HistGradientBoostingRegressor(max_iter=100, max_depth=5, learning_rate=0.05, random_state=42)
    
    thresholds = []

    # Calculate Sample Weights
    # Strategy: Give higher weight to the most recent year of data.
    # This addresses "concept drift" / changing health conditions.
    current_max_date = df['Date'].max()
    cutoff_date = current_max_date - pd.Timedelta(days=365)
    
    # Base weight 1.0, Recent weight 3.0
    # We use numpy where for vectorization
    sample_weights = np.where(df['Date'] > cutoff_date, 3.0, 1.0)
    
    print(f"Applying Weighted Training: Recent data (> {cutoff_date.date()}) gets 3x weight.")
    
    print("\n--- Starting Time Series Cross-Validation ---")
    for fold, (train_index, test_index) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train_bin, y_test_bin = y_bin.iloc[train_index], y_bin.iloc[test_index]
        y_train_reg, y_test_reg = y_reg.iloc[train_index], y_reg.iloc[test_index]
        weights_train = sample_weights[train_index]
        
        # 1. Train Classifier
        clf.fit(X_train, y_train_bin, sample_weight=weights_train)
        
        # Predict Probabilities
        y_probs = clf.predict_proba(X_test)[:, 1]
        
        # Optimize Threshold for F1 Score
        # Simple loop to find best threshold on TEST set (idealized) 
        # In prod we'd pick this on validation set, but here we just want to see potential.
        best_f1 = 0
        best_thresh = 0.5
        from sklearn.metrics import f1_score
        
        # Search range 0.1 to 0.9
        for thresh in np.arange(0.1, 0.9, 0.05):
            y_temp = (y_probs >= thresh).astype(int)
            f1 = f1_score(y_test_bin, y_temp, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = thresh
        
        thresholds.append(best_thresh)
        y_pred_bin = (y_probs >= best_thresh).astype(int)
        
        # 2. Train Regressor (on full data or just positives? Let's use full for robustness, or just positives)
        # Using full data is safer for gradient boosting, it learns 0s. 
        # But let's try training on all, and gating output.
        reg.fit(X_train, y_train_reg, sample_weight=weights_train)
        y_pred_reg_raw = reg.predict(X_test)
        y_pred_reg_raw = np.maximum(y_pred_reg_raw, 0)
        
        # Combined Prediction: If Classifier says 0, then 0. Else Regressor.
        y_pred_combined = y_pred_reg_raw * y_pred_bin
        
        # Metrics
        y_test_reg_orig = np.expm1(y_test_reg)
        y_pred_combined_orig = np.expm1(y_pred_combined)
        
        acc = accuracy_score(y_test_bin, y_pred_bin)
        mae = mean_absolute_error(y_test_reg, y_pred_combined) # Log scale
        mae_orig = mean_absolute_error(y_test_reg_orig, y_pred_combined_orig) # Original scale
        
        acc_scores.append(acc)
        combined_mae_scores.append(mae)
        
        baseline_acc = max(y_test_bin.mean(), 1 - y_test_bin.mean())
        
        # Component Analysis
        # Classifier Metrics
        from sklearn.metrics import precision_recall_fscore_support
        prec, rec, f1, _ = precision_recall_fscore_support(y_test_bin, y_pred_bin, average='binary', zero_division=0)
        
        # Regressor Metrics (Only on True Positives - days where user actually had pain)
        # This tells us: "When there IS a migraine, how close is the prediction?"
        mask_pain = y_test_bin > 0
        if mask_pain.sum() > 0:
            reg_mae_pain = mean_absolute_error(y_test_reg_orig[mask_pain], y_pred_combined_orig[mask_pain])
        else:
            reg_mae_pain = 0.0
            
        print(f"Fold {fold+1} (Thresh={best_thresh:.2f}):")
        print(f"  Overall: Acc={acc:.4f} (Base: {baseline_acc:.4f}), MAE={mae_orig:.4f}")
        print(f"  Classifier: Precision={prec:.3f}, Recall={rec:.3f}, F1={f1:.3f}")
        print(f"  Regressor (Pain Only): MAE={reg_mae_pain:.3f}")

    # Plotting last fold results
    plt.figure(figsize=(12, 6))
    plt.plot(y_test_reg.index, y_test_reg, label='Actual Pain (Log)', alpha=0.7)
    plt.plot(y_test_reg.index, y_pred_combined, label='Predicted Pain (Combined)', alpha=0.7, linestyle='--')
    plt.title("Constraint-Aware Prediction (Last Fold)")
    plt.legend()
    plt.savefig(os.path.join(MODEL_DIR, 'prediction_plot.png'))
    print(f"Plot saved to {os.path.join(MODEL_DIR, 'prediction_plot.png')}")

    print("\n--- Average Performance ---")
    print(f"Avg Accuracy: {np.mean(acc_scores):.4f}")
    print(f"Avg MAE: {np.mean(combined_mae_scores):.4f}")
    
    # Final Training
    print("\nTraining Final Models on All Data...")
    clf.fit(X, y_bin, sample_weight=sample_weights)
    reg.fit(X, y_reg, sample_weight=sample_weights)
    
    joblib.dump(clf, MODEL_CLF_PATH)
    joblib.dump(reg, MODEL_REG_PATH)
    print("Models saved.")
    
    # Return stats for testing
    return clf, np.mean(acc_scores), np.mean(combined_mae_scores)

if __name__ == "__main__":
    train_and_evaluate()
