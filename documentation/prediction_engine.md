# Advanced Prediction Engine

Migraine Navigator employs a sophisticated **Hybrid Architecture** to solve the "Cold Start" problem inherent in pure ML systems.

## Hybrid Architecture

### 1. Bayesian Heuristic Engine (New Users)
Provides immediate, personalized predictions from Day 1. It bridges the "Cold Start" gap by using your calibrated settings (sensitivity to Weather, Sleep, Stress) until sufficient history exists.

### 2. Gradient Boosting ML (Established Users)
Automatically takes over once enough data is collected (typically >30 logs) to detect complex, non-linear patterns unique to your biology using Gradient Boosting Decision Trees (GBDT).

## 24-Hour Risk Engine (Truth Propagation)

Training a pure ML model for hourly predictions requires unrealistic, massive labeled datasets with hourly log entries. We solve this with a 3-step hybrid approach:

*   **Step 1 (The Anchor)**: The powerful and proven Daily ML Model predicts the overall risk intensity for the day (e.g., "69% Risk") based on deep historical patterns.
*   **Step 2 (The Curve)**: A granular Heuristic Engine calculates the relative risk for every hour based on circadian rhythms, weather shifts (Open-Meteo), and medication half-lives.
*   **Step 3 (The Calibration)**: The hourly curve is mathematically scaled so that its peak matches the Daily ML "Truth". 

**Result**: This provides the best of both worlds: the **accuracy** of the ML model with the **temporal resolution** of the heuristic engine.

## Enhanced Triggers
The engine now accounts for detailed meteorological factors:
*   Rain (>0.5mm)
*   High Humidity (>70%)
*   Pressure Instability (Rapid drops or spikes)
