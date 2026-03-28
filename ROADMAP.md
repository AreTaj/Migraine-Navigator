# Future Roadmap

Development is organized into phased milestones to ensure stability and focus.

## [v0.3.0] Core Architecture & Stability (Completed)
*Focus: Refactoring, robustness, and background infrastructure.*
- **[Issue #45] Extract Service Logic from API Routes** (Completed)
- **[Issue #46] Refactor Training Loop (Decouple Config)** (Completed)
- **[Issue #53] Use Memory Mapping for Model Loading** (Completed)
- **[Issue #42] Implement Dynamic Port Discovery for Sidecar Backend** (Completed)
- **[Issue #50] Data Import System** (Completed)
- **[Issue #52] Automatic Periodic Model Retraining** (Completed)
- **[Issue #59] Implement Feature Selection via Correlation Matrix** (Completed)

## [v0.3.2] Adaptive Weather Patch
*Focus: Implement Adaptive Weather Sensitivity to properly trigger alerts based on local climate rather than hardcoded heuristics.*
- **[Issue #66] Weather Cache Backfill: Populate history for new users via Open-Meteo daily API**
- **[Issue #67] Adaptive Pressure Threshold: Replace hardcoded 8 hPa cap with percentile-based sensitivity**
- **[Issue #68] Adaptive Heat Stress Detection: Rolling mean temperature deviation trigger**

## [v0.4.0] User Experience & Onboarding
*Focus: Interface polish, user journey, and first-time experience.*
- **[Issue #36] Feature Request: Dashboard UI Overhaul & Risk Decomposition** (Completed)
- **[Issue #48] New User Onboarding Flow**
- **[Issue #49] Settings Tab**
- **[Issue #61] Dashboard Frontend Implementation**

## [v0.5.0] Advanced Analytics
*Focus: Upgrade weather data inputs, model explainability features, and medication analytics.*
- **[Issue #60] Implement Correlation Matrix Filtering** (Completed)
- **[Issue #27] Medication Effectiveness Metric**
- **[Issue #28] Global Feature Importance Analysis**
- **[Issue #54] Barometric Crash Detector**
- **[Issue #55] Instability Index (temp_hourly_std)**
- **[Issue #56] Heat Stress Load**
- **[Issue #57] Wet Bulb Interaction (max_dew_point)**
- **[Issue #58] Statistical Shape Features**
- **[Issue #62] Dashboard Backend Risk Explanation (SHAP)**

## [v0.6.0] The Simulator
*Focus: Interactive "What-If" prediction, travel risk forecasting, and simulation UI.*
- **[Issue #30] Feature Request: Migraine Simulator (What-If Analysis)** (Completed)
- **[Issue #51] Travel Migraine Risk Simulator**
- **[Issue #63] Migraine Simulator API Endpoint**
- **[Issue #64] Migraine Simulator UI**
