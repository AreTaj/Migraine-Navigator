from datetime import datetime
from typing import Dict, Any

class HeuristicPredictor:
    """
    A rule-based predictor for the "Cold Start" phase (Phase 1) of the Hybrid Prediction Engine.
    Calculates migraine risk based on weighted user sensitivities to environmental and biological factors.
    """
    
    def __init__(self, user_priors: Dict[str, float] = None):
        """
        Initialize with user-specific sensitivity weights.
        If no priors are provided, defaults to neutral weights (0.5).
        
        Args:
            user_priors: Dictionary containing keys:
                - 'baseline_risk': 0.0-1.0 (Base rate of migraines)
                - 'weather_sensitivity': 0.0-1.0
                - 'sleep_sensitivity': 0.0-1.0 
                - 'strain_sensitivity': 0.0-1.0
        """
        self.priors = user_priors or {
            'baseline_risk': 0.1,      # Default: Rare
            'weather_sensitivity': 0.5,
            'sleep_sensitivity': 0.5,
            'strain_sensitivity': 0.5
        }

    def predict(self, weather_data: Dict[str, Any], sleep_data: float = 0.0, strain_data: float = 0.0, yesterday_pain: float = 0.0) -> Dict[str, Any]:
        """
        Calculate risk score based on the weighted linear equation.
        
        Formula:
        Risk = Baseline + (Weather * Weight) + (Sleep * Weight) + (Strain * Weight) + (Cluster * Weight)
        
        Args:
            weather_data: Dictionary containing 'pressure_change', 'prcp', 'average_humidity', etc.
            sleep_data: Hours of sleep debt (or raw sleep quality inverse).
            strain_data: Physical/Mental strain level (0-10).
            yesterday_pain: Pain level of the previous day (0-10).
            
        Returns:
            Dictionary with 'probability' (0-1), 'risk_level', and 'components'.
        """
        
        # 1. Baseline Risk
        base_risk = self.priors.get('baseline_risk', 0.1)
        risk_score = base_risk
        
        # 2. Weather Impact
        # Pressure - We use abs() because both rapid DROPS and SPIKES can be triggers.
        # Any instability > 8hPa is considered maximum risk.
        pressure_delta = abs(weather_data.get('pressure_change', 0.0))
        weather_score = min(pressure_delta / 8.0, 1.0) # Cap at 8hPa change
        
        # Rain (Precipitation) - Presence of rain adds risk
        if weather_data.get('prcp', 0) > 0.5:
            weather_score += 0.3
            
        # Humidity - High humidity (>70%) adds risk
        humidity = weather_data.get('average_humidity', 50)
        if humidity > 70:
            weather_score += 0.2
            
        # Normalize and apply sensitivity
        weather_risk_contribution = min(weather_score, 1.0)
        risk_score += weather_risk_contribution * self.priors.get('weather_sensitivity', 0.5) * 0.5
        
        # 3. Sleep Impact (Now Active)
        # Sleep debt > 0 implies risk. 
        # We assume sleep_data is "Sleep Debt Hours" (0-4+)
        normalized_sleep_risk = min(sleep_data / 4.0, 1.0)
        risk_score += normalized_sleep_risk * self.priors.get('sleep_sensitivity', 0.5) * 0.3
        
        # 4. Physical/Mental Strain Impact (Now Active)
        # Strain is 0-10
        normalized_strain = strain_data / 10.0
        risk_score += normalized_strain * self.priors.get('strain_sensitivity', 0.5) * 0.3
        
        # 5. Cluster / Persistence Effect
        # If yesterday had pain > 0, we boost today's risk.
        # However, we scale this boost by the user's 'baseline_risk'.
        # Rationale: A user with "Chronic" (High Baseline) is much more likely to have clusters 
        # than a user with "Rare" (Low Baseline) migraines.
        cluster_boost = 0.0
        if yesterday_pain > 2.0: # Threshold for "Migraine took place"
            # Boost = Base * 0.5 (e.g., Rare=0.05 boost, Chronic=0.3 boost)
            cluster_boost = base_risk * 0.8 
            risk_score += cluster_boost
        
        # Clamp result
        final_probability = min(max(risk_score, 0.0), 1.0)
        
        return {
            "probability": round(final_probability, 2),
            "risk_level": self._get_risk_level(final_probability),
            "source": "Heuristic (Phase 1)",
            "components": {
                "baseline": base_risk,
                "weather_contribution": round(weather_risk_contribution, 2),
                "cluster_boost": round(cluster_boost, 2)
            }
        }

    def _get_risk_level(self, probability: float) -> str:
        if probability < 0.3:
            return "Low"
        elif probability < 0.7:
            return "Moderate"
        else:
            return "High"

    def predict_hourly(self, weather_data: Dict[str, Any], circadian_probability: float, medication_recency: float = None) -> Dict[str, Any]:
        """
        Calculate hourly risk score (Hybrid: Heuristic + Statistical + Intervention).
        
        Args:
            weather_data: Hourly weather snapshot (must include 'pressure_change_3h', 'prcp', 'humidity').
            circadian_probability: 0.0-1.0 score based on historical start times for this hour.
            medication_recency: Hours since last acute medication (or None if none taken).
            
        Returns:
            Dictionary with 'probability' (0-1), 'risk_level', and components.
        """
        
        # 1. Base Risk (Heuristic Weather)
        # Pressure: We use 3-hour delta. Sensitivity is higher for short bursts.
        # Rule: 3hpa drop in 3 hours is significant.
        pressure_delta = abs(weather_data.get('pressure_change_3h', 0.0))
        weather_score = min(pressure_delta / 3.0, 1.0) # Cap at 3hPa change
        
        if weather_data.get('prcp', 0) > 0.5:
            weather_score += 0.3
            
        if weather_data.get('humidity', 50) > 70:
            weather_score += 0.2
            
        heuristic_risk = min(weather_score, 1.0) * self.priors.get('weather_sensitivity', 0.5)
        
        # 2. Circadian Risk (Statistical)
        # This acts as a rolling baseline. If it's a "bad time of day", risk floor is raised.
        # We weigh this heavily as it captures biological rhythm.
        circadian_risk = circadian_probability * 1.0 # 1:1 mapping
        
        # Combine Pre-Mitigation Risk
        # "Nature + Nurture" (Weather + Bio)
        # We take the Maximum of the two signals, damped by the other? 
        # Or a weighted sum. Let's do weighted sum where History sets the stage and Weather triggers it.
        
        # Formula: Base = Circadian (30%) + Weather (70%)? 
        # Actually, if Circadian is 0, Weather can still trigger.
        # If Weather is 0, Circadian (high stress time) can still trigger.
        raw_risk = (heuristic_risk * 0.6) + (circadian_risk * 0.4)
        
        # Boost if both are high (Interaction)
        if heuristic_risk > 0.5 and circadian_risk > 0.5:
            raw_risk += 0.2
            
        # 3. Medication Shield (Intervention)
        # If taken recently, risk is crushed.
        mitigation_factor = 1.0
        if medication_recency is not None:
            # Model: Complete shield for 2 hours, then linear decay to 6 hours.
            if medication_recency < 2.0:
                mitigation_factor = 0.1 # 90% protection
            elif medication_recency < 6.0:
                # Decay from 0.1 to 1.0 over 4 hours
                # slope = 0.9 / 4 = 0.225
                # factor = 0.1 + (recency - 2) * 0.225
                mitigation_factor = 0.1 + ((medication_recency - 2.0) * 0.225)
            else:
                mitigation_factor = 1.0
        
        final_probability = min(max(raw_risk * mitigation_factor, 0.0), 1.0)
        
        return {
            "probability": round(final_probability, 2),
            "risk_level": self._get_risk_level(final_probability),
            "source": "Hybrid Hourly",
            "components": {
                "heuristic_weather": round(heuristic_risk, 2),
                "circadian_risk": round(circadian_risk, 2),
                "mitigation_factor": round(mitigation_factor, 2)
            }
        }

