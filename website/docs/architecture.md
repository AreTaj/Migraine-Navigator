---
sidebar_position: 1
title: System Overview
---

# Migraine Navigator: Technical System Overview
**Current Version:** v0.2.5
**Scope:** Hybrid AI Architecture, Data Analytics, and System Design

---

## 1. System Architecture
The application follows a modern **Service-Oriented Architecture (SOA)** tailored for a desktop environment via Tauri.

* **Frontend (Presentation Layer)**:
    * **Framework**: React 18 (Vite)
    * **Visualization**: Recharts (D3-based) for high-performance time-series rendering.
    * **State Management**: React Hooks + Local Component State (optimized for reduced complexity).
* **Backend (Application Layer)**:
    * **Server**: FastAPI (Python 3.10+), running as a sidecar subprocess.
    * **API Protocol**: RESTful JSON over localhost.
* **Persistence (Data Layer)**:
    * **Database**: SQLite3 (Embedded). Ideal for single-user desktop privacy and zero-config deployment.
    * **ORM/DAO**: Custom Data Access Objects (`EntryService`) using raw SQL for maximum performance control and explicit schema management.

---

## 2. Advanced Prediction Engine (Hybrid Architecture)
The core value proposition of Migraine Navigator is its predictive engine, which employs a **Hybrid Strategy** to forecast migraine risk. This approach solves the "Cold Start" problem inherent in pure ML systems.

### 2.1 Hybrid Strategy
1.  **Bayesian Heuristic Engine (New Users)**: 
    *   Provides immediate, personalized predictions from Day 1.
    *   Bridges the gap until sufficient history exists by utilizing user-calibrated settings (sensitivity to Weather, Sleep, Stress).
2.  **Gradient Boosting ML (Established Users)**: 
    *   Automatically takes over once enough data is collected (typically ~30-50 logs).
    *   Detects complex, non-linear patterns unique to your biology using **Gradient Boosting Decision Trees (GBDT)** via `scikit-learn`.

### 2.2 The 24-Hour Risk Engine ("Truth Propagation")
Training a pure ML model for hourly predictions requires unrealistic, massive labeled datasets (hourly logs). We solve this with a 3-step hybrid approach:

1.  **Step 1 (The Anchor)**: The proven **Daily ML Model** predicts the overall risk intensity for the day (e.g., "69% Risk") based on deep historical patterns.
2.  **Step 2 (The Curve)**: A granular **Heuristic Engine** calculates relative risk for every hour based on circadian rhythms, real-time weather shifts (Open-Meteo), and medication half-lives.
3.  **Step 3 (Calibration)**: The hourly curve is mathematically scaled so that its peak matches the Daily ML "Truth". 
    *   *Result*: The **accuracy** of the ML model + the **temporal resolution** of the heuristic engine.

### 2.3 Feature Engineering (`predict_future.py`)
Raw data is transformed into a dense feature vector X containing ~24 dimensions:

* **Temporal Features**:
    * Cyclical Encoding: `DayOfWeek_sin`, `DayOfWeek_cos`. Preserves the proximity between "Sunday" and "Monday".
* **Meteorological Features**:
    * **Thermodynamics**: Temperature (T_max, T_min), Humidity (H_rel > 70%).
    * **Barometrics**: Surface Pressure and **Pressure Instability** (24h Delta).
* **Autoregressive (Lag) Features**:
    * Captures the "Memory" of the disease (Lags: t-1 to t-7 days).
    * **Rolling Statistics**: Detection of flare-up clusters.

---

## 3. Data Analytics & Visualization

### 3.1 Real-time Aggregation
* **Dynamic Metrics**: Calculations like "Average Days/Month" are computed dynamically based on the actual data span.
* **Medication Analysis**: "Pain-Based" usage tracking that filters out pain-free days for more accurate frequency analysis.

### 3.2 Forecasting Engine
* **Recursive Forecasting**: The 7-Day Forecast simulates the future day-by-day, allowing "Cluster" patterns (migraines following migraines) to emerge naturally.
* **Caching Strategy**: Predictions are cached in-memory with a 1-hour TTL (Time-To-Live) to prevent API rate-limiting.

---

## 4. Key Technologies
* **Core ML**: `scikit-learn`, `numpy`, `pandas`, `joblib`.
* **Server**: `uvicorn`, `fastapi`, `pydantic`.
* **External Data**: Open-Meteo (Free, Non-Commercial License compatible for personal tools).

---

## 5. Licensing
**Source-Available (PolyForm Noncommercial 1.0.0)**
*   **Privacy-First**: Personal health data never leaves the user's machine.
*   **Transparency**: The codebase opens the "black box" on how the AI works, without surrendering commercial rights.