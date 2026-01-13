# Clinician’s Overview: Migraine Navigator
**Target Audience:** Neurologists, General Practitioners, and Pain Management Specialists  
**Technical Basis:** Local-First Supervised Learning & Hybrid Heuristics

---

## **Technical Briefing for Clinicians: Executive Summary**
*   **The Problem**: Subjective patient recall of migraine triggers is often inaccurate or incomplete.
*   **The Solution**: A local-first desktop application that correlates user-logged symptoms with high-resolution environmental data (barometric pressure, humidity, etc.).
*   **The Tech**: Uses **Gradient Boosting (GBDT)** for individualized (N-of-1) risk modeling.
*   **The Clinical Value**: Provides quantitative data to help identify triggers and evaluate prophylactic/acute treatment efficacy.
*   **Privacy**: **Local-first architecture.** Data never leaves the patient's device, ensuring maximum security and zero PII transmission.

---

## 1. Project Objective
Migraine Navigator is designed to augment the personal feedback loop by providing **quantitative, prospective environmental and behavioral logs** to complement user recall. 

By correlating high-resolution meteorological data with patient-logged symptoms and lifestyle factors, the tool generates a personalized "Risk Profile" that can help clinicians identify potential patterns and observe the impact of lifestyle modifications.

## 2. Methodology & Evidence
The application employs a dual-stage predictive pipeline to calibrate performance from the first day of use (the "Cold Start" problem) through long-term observation.

### 2.1 The Hybrid Engine
*   **User-Configurable Heuristic Engine**: For new patients with limited data (< 60 entries), the system uses a weighted scoring algorithm. Users configure their own sensitivity to factors like Weather, Sleep, and Strain via the settings. Default values are provided as neutral starting points but are not clinical assertions.
*   **Dual-Stage Hurdle Model (GBDT)**: As the patient's longitudinal dataset grows (N > 60 entries), the system transitions to a personalized **Hurdle Model**. Because migraine data is "zero-inflated" (many pain-free days), a single regression model often struggles. We solve this by splitting the problem:
    1.  **Classifier (The Gate)**: A Binary GBDT predicts the *probability* of a migraine occurring.
    2.  **Regressor (The Severity)**: A GBDT Regressor predicts the *intensity* (1-10) if a migraine occurs.
    The final risk profile is a product of these two models, capturing non-linear interactions unique to that specific patient’s biology.

### 2.2 Truth Propagation (Temporal Detail)
To provide granular hourly risk assessment without requiring the patient to log every hour, the system uses a **"Truth Propagation"** algorithm. It uses the Daily ML Prediction as a statistical baseline and scales a high-resolution hourly heuristic curve (based on circadian rhythms and real-time weather shifts) to match that anchor.

## 3. Data Integrity & Privacy (Clinician Safeguards)
One of the primary barriers to digital health adoption is data security. Migraine Navigator solves this through a **Local-First Architecture**:

*   **Zero-Cloud Footprint**: All patient logs, medication history, and ML model weights are stored in an encrypted SQLite database **locally on the patient's device**. 
*   **No PII Transmission**: No personally identifiable information (PII) or health data is ever transmitted to external servers. Weather data is fetched via anonymized coordinates.
*   **HIPAA/GDPR Alignment**: Because the developer never possesses the data, the risk of data breaches or unauthorized access is eliminated by design.

## 4. Interpreting Patient Reports

### 4.1 Current Clinical Utility
*   **Trigger Registry**: Reviewing the patient's "Usage Count" for various triggers helps confirm if perceived triggers (e.g., "Chocolate," "Stress") align with their actual log frequency.
*   **Environmental Logs**: Providing a high-resolution history of weather conditions (Pressure, Humidity) alongside pain onset to validate or rule out weather sensitivity.

### 4.2 Roadmap Capabilities (In Development)
*   **Risk Decomposition (XAI)**: Future updates will visualize *why* a specific day is flagged (e.g., "High Risk due to 15hPa pressure drop + Sleep Debt").
*   **Medication Efficacy Analysis**: Statistical tracking of "Pain Decay" curves—calculating the mean time-to-relief for different acute interventions to optimize personalized care plans.
*   **Travel Risk Simulator**: A predictive tool to assess migraine risk at potential travel destinations based on their local climate profiles.

---

> [!IMPORTANT]
> **Clinical Disclaimer**: Migraine Navigator is a decision-support tool, not a diagnostic or treatment device. It provides statistical probabilities based on historical patterns. Treatment changes should always be supervised by a licensed medical professional.
