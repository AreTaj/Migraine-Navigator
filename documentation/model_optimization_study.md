# Migraine Risk Model Analysis: The "Perfect Storm" Simulation
**Date:** December 16, 2025  
**Subject:** Optimization Study of Predictive Triggers

---

## Part 1: Executive Summary
**Audience:** Users, Product Managers, Stakeholders

### The Question
> [!NOTE]
> **Dataset Scope**: This study analyzes a model trained exclusively on **single-patient historical data (N=1)**. The identified triggers and risk probabilities are highly personalized to this specific user's biological patterns and environmental sensitivity. They do not represent clinical generalizations for the broader migraine population.

Can we identify the absolute worst-case scenario for a migraine sufferer? By reverse-engineering our predictive AI, we sought to find the precise combination of weather and lifestyle choices that guarantees a migraine.

### The "Stress Test"
Think of this as a crash test for the digital brain. Rather than ask the AI "will I get a migraine today?", we forced it to simulate **80,640 different days**, ranging from the virtual equivalent of perfect weather vacations to stressful, stormy work weeks. We tweaked every dial—temperature, pressure, sleep quality, activity levels, and even the day of the week—to find the worst possible breaking point.

### The "Perfect Storm" Result (91.2% Risk)
The model identified a specific set of conditions that created a near-certainty (**91.2%**) of a migraine attack:
*   **The Timing**: A **Monday**.
*   **The Weather**: A hot **35°C (95°F)** day combined with a sharp drop in barometric pressure (**990 hPa**—typical of an incoming storm front).
*   ** The Behavior**: Crucially, the weather alone wasn't enough. The risk peaked only when combined with **Poor Sleep** and **Zero Physical Activity**.

### Key Takeaway
The AI justifies (though maybe not yet proves) a hypothesis that we've all probably heard before: **Lifestyle acts as a buffer.** Even in the worst weather conditions, improving sleep or activity levels in the simulation dropped the risk from "Critical" to "High" or "Moderate." You cannot control the weather, but you can control the outcome.

---

## Part 2: Technical Analysis
**Audience:** Data Scientists, ML Engineers, Developers

### Methodology: Brute-Force Grid Search
To identify the global maximum for $P(Migraine | X)$, we implemented a Cartesian Grid Search algorithm iterating over a discretized feature space of $N=80,640$ vectors.

**Feature Space Dimensions:**
*   **$T_{avg}$ (Temperature)**: `[5.0, 15.0, 25.0, 35.0]` (Celsius)
*   **$P_{surface}$ (Pressure)**: `[990.0, 1000.0, 1015.0, 1030.0]` (hPa)
*   **$H_{rel}$ (Humidity)**: `[20.0, 50.0, 80.0]` (%)
*   **$\Delta P$ (Pressure Change)**: `[-5.0 ... 5.0]` (hPa/24h)
*   **$S_{qual}$ (Sleep)**: `[1.0, 2.0, 3.0]` (Ordinal Scale)
*   **$A_{phys}$ (Activity)**: `[0.0, 1.0, 2.0, 3.0]` (Ordinal Scale)
*   **$L_{pain}$ (Lag History)**: `[0.0, 3.0, 7.0, 9.0]` (Pain Magnitude)
*   **$D_{week}$ (Day of Week)**: `[0, ..., 6]` (Mon-Sun)

### Optimization Logic
The script (`tests/maximize_risk.py`) initializes the trained Gradient Boosting Classifier. For each permutation vector $v_i$:
1.  Construct a synthetic feature matrix $X_i$.
2.  Override scalar keys with $v_i$ components.
3.  Compute inference: $\hat{y}_i = \text{clf.predict\_proba}(X_i)[1]$.
4.  Update $\theta_{max}$ if $\hat{y}_i > \theta_{current}$.

### Results & Feature Interaction
The convergence on **91.2%** probability reveals high non-linearity in the decision trees.
*   **The "Monday" Factor**: Including the Day of Week increased the risk ceiling from 91.1% to 91.2%. While the model identified **Monday** as the highest-risk day, the marginal impact (+0.1%) suggests that while cyclical stressors exist, biological and meteorological factors are far more dominant.
*   **Interaction Effect**: The model shows a strong interaction between **Low Pressure** and **High Temperature**.
*   **History Sensitivity**: Interestingly, a *Moderate* recent pain history (3.0 vs 9.0) yielded higher immediate risk. This suggests the model has learned a "prodrome" or "buildup" pattern, where mid-level pain predicts a future spike better than already-peak pain (which might indicate the attack is subsiding).
*   **Dominant Factors**: Sleep quality ($S_{qual}$) functioned as a primary gatekeeper; values of $S_{qual} \ge 2.0$ significantly dampened the maximum achievable risk, regardless of weather vectors.
