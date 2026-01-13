# Medical Research Overview: Migraine Navigator
**Focus:** Longitudinal Tracking, N-of-1 Methodology, and Machine Learning Validity

---

## 1. Research Objective
Migraine Navigator serves as a platform for **high-resolution longitudinal tracking**. The project explores how individualized (N-of-1) machine learning models can identify latent environmental and behavioral triggers that are often obscured in large-scale population studies due to physiological heterogeneity.

## 2. Statistical Methodology
The platform addresses the classic "small data" challenge in personalized health through a phased architecture involving a **User-Configurable Heuristic** (Phase 1) and **Machine Learning** (Phase 2):

### 2.1 Gradient Boosting Decision Trees (GBDT) & The Hurdle Model
Migation tracking data is inherently "zero-inflated"—patients have many more healthy days than sick days. Standard regression models often "average out" these zeros, leading to under-prediction of severe events. We utilize a **Two-Stage Hurdle Model** (`Scikit-Learn`) to address this:

1.  **Binary Classification Stage**: Estimates the probability of $Pain > 0$.
2.  **Regression Stage**: Estimates the log-severity of pain, conditional on $Pain > 0$.

This approach allows us to:
*   **Handle Variance**: Accurately model both the *occurrence* and the *severity* independently.
*   **Capture Non-Linear Interactions**: Identify synergistic risks (e.g., combined barometric pressure drops and sleep deprivation) that linear models (Logistic Regression) may underestimate.

### 2.2 Feature Engineering & Encoding
*   **Cyclical Temporal Encoding**: Days of the week and months are transformed using sine/cosine transforms to preserve the mathematical proximity of cyclical boundaries (e.g., ensuring Monday is as "close" to Sunday as it is to Tuesday).
*   **Meteorological Resolution**: Integrating hourly historical and forecast data (Open-Meteo) to capture volatility markers, such as the **stability index** (24-hour barometric delta).

## 3. The N-of-1 Paradigm
By focusing on the individual as their own control, the model avoids the "mean-field" error where population-level averages fail to capture a specific patient's idiosyncratic triggers. This methodology is particularly relevant for diseases with high symptomatic variance like migraines.

## 4. Potential Research Applications
*   **Trigger Identification**: Quantifying the lag-time between weather events and symptom onset.
*   **Medication Response Variability**: Analyzing the "pain decay" curve of different acute interventions in a real-world setting.
*   **Prodromal Analysis**: Using autoregressive features (lagged pain states) to identify potential digital markers of the prodromal phase.
*   **Explainable AI (XAI)**: Future integration of SHAP (SHapley Additive exPlanations) to decompose daily risk into marginalized feature contributions (e.g. visualizing the specific weight of "Sleep Debt" vs "Barometric Pressure" for a given prediction).

---

## 5. Data Privacy & Ethics
To facilitate trust and ethical research:
*   **Edge Computing**: All model training and inference occur locally on the user's machine.
*   **Zero-Server Persistence**: This architecture demonstrates a path forward for "Privacy-Preserving ML" in highly sensitive medical domains.
