# Migraine Navigator: Technical System Overview
**Date:** December 16, 2025
**Scope:** Data Analytics, AI/ML Architecture, and System Design

---

## 1. System Architecture
The application follows a modern **Service-Oriented Architecture (SOA)** tailored for a desktop environment via Tauri.

*   **Frontend (Presentation Layer)**:
    *   **Framework**: React 18 (Vite)
    *   **Visualization**: Recharts (D3-based) for high-performance time-series rendering.
    *   **Services Layer**: Decoupled API logic (`medicationService`, `triggerService`, `entryService`) to abstract database interactions from UI components.
    *   **State Management**: React Hooks + Local Component State (optimized for reduced complexity).
*   **Backend (Application Layer)**:
    *   **Server**: FastAPI (Python 3.10+), running as a sidecar subprocess.
    *   **API Protocol**: RESTful JSON over localhost.
*   **Persistence (Data Layer)**:
    *   **Database**: SQLite3 (Embedded). Ideal for single-user desktop privacy and zero-config deployment.
    *   **ORM/DAO**: Custom Data Access Objects (`EntryService`) using raw SQL for maximum performance control and explicit schema management.

---

## 2. Artificial Intelligence & Machine Learning Pipeline
The core value proposition of Migraine Navigator is its predictive engine, which employs **Supervised Learning** to forecast migraine risk.

### 2.1 Model Architecture
We utilize a dual-model approach using **Gradient Boosting Decision Trees (GBDT)** via `scikit-learn`.
1.  **Risk Classifier (`GradientBoostingClassifier`)**:
    *   **Task**: Binary Classification (Will a migraine occur? Yes/No).
    *   **Output**: Probability Score ($P \in [0, 1]$).
    *   **Calibration**: Threshold-tuned (e.g., $>0.2$ = Moderate Risk) based on user sensitivity.
2.  **Severity Regressor (`GradientBoostingRegressor`)**:
    *   **Task**: Regression (Predicted Pain Level 0-10).
    *   **Target**: Log-transformed Pain Level ($\log(1 + y)$) to handle zero-inflated targets and enforce non-negativity.

### 2.2 Feature Engineering (`predict_future.py`)
Raw data is transformed into a dense feature vector $X$ containing ~24 dimensions:

*   **Temporal Features**:
    *   Cyclical Encoding: `DayOfWeek_sin`, `DayOfWeek_cos`, `Month_sin`, `Month_cos`. This preserves the proximity between "Sunday" (6) and "Monday" (0).
*   **Meteorological Features** (Source: Open-Meteo API):
    *   **Thermodynamics**: Temperature ($T_{max}, T_{min}, T_{avg}$), Humidity ($H_{rel}$).
    *   **Barometrics**: Surface Pressure ($P_{surf}$) and 24-hour Delta ($\Delta P$).
    *   **Solar**: Sunshine Duration (Minutes).
*   **Autoregressive (Lag) Features**:
    *   Captures the "Memory" of the disease.
    *   **Lags**: $t_{-1}, t_{-2}, t_{-3}, t_{-7}$ days.
    *   **Rolling Statistics**: Rolling Mean (3-day, 7-day window) to detect flare-up clusters.
*   **Lifestyle Inputs**:
    *   Sleep Quality (Ordinal 1-3) and Physical Activity (Ordinal 0-3).
    *   *Note: Missing values are imputed with medians (`2.0`, `1.5`) to prevent model drift.*

---

## 3. Data Analytics & Visualization
The analytics engine transforms raw logs into actionable intelligence on the client side.

### 3.1 Real-time Aggregation (`Dashboard.jsx`)
*   **Dynamic Metrics**: Calculations like "Average Days/Month" are computed dynamically based on the *actual* data span (e.g., dividing by 3 months for a new user vs 12 for an existing one).
*   **Unit Consistency**: Strict type enforcement ensures alignment between Backend (Integers/Floats) and Frontend (Strings from Forms).

### 3.2 Forecasting Engine
*   **Batch Processing**: The 7-Day Forecast generates predictions in bulk. It fetches a single JSON packet from Open-Meteo containing 7 days of hourly data, processes it into 7 feature vectors, and runs batch inference in $<0.8s$.
*   **Caching Strategy**: Predictions are cached in-memory with a 1-hour TTL (Time-To-Live). This prevents API rate-limiting and ensures instant dashboard reloads.

---

## 4. Key Technologies
*   **Core ML**: `scikit-learn`, `numpy`, `pandas`, `joblib`.
*   **Server**: `uvicorn`, `fastapi`, `pydantic`.
*   **External Data**: Open-Meteo (Free, Non-Commercial License compatible for personal tools).

## 5. Process Management & Deployment

To ensure robustness across both **Development** and **Production** environments without manual configuration, the system employs an automated build-profile detection strategy.

### 5.1 Automated Sidecar Management
The Tauri frontend (`src-tauri/src/lib.rs`) effectively operates as a process manager for the Python backend. It utilizes Rust's conditional compilation features (`#[cfg(not(debug_assertions))]`) to determine the environment:

*   **Development Profile (Debug)**:
    *   **Sidecar**: DISABLED. The Rust shell command to spawn the backend is compiled out.
    *   **Backend**: Developer manually executes `uvicorn api.main:app` (hot-reloading enabled).
    *   **Database**: Resolves to `<ProjectRoot>/data/migraine_log.db`.

*   **Release Profile (Production)**:
    *   **Sidecar**: ENABLED. The application automatically spawns the compiled/frozen backend binary (`migraine-navigator-api`).
    *   **Stdin Monitoring**: The backend listens to `sys.stdin`. If the parent Tauri process closes the pipe (i.e., app exit or crash), the Python backend self-terminates instantly, preventing "zombie" processes.
    *   **Database**: automatically resolves to the User Data Directory (e.g., `~/Library/Application Support/MigraineNavigator/migraine_log.db` on macOS) to comply with OS sandboxing and persistence standards.

