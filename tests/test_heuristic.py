import pytest
from forecasting.heuristic_predictor import HeuristicPredictor

def test_heuristic_defaults():
    predictor = HeuristicPredictor()
    # Default baseline is 0.1
    # Neutral input (0 weather, 0 sleep, 0 strain)
    result = predictor.predict({'pressure_change': 0.0})
    assert result['probability'] == 0.1
    assert result['risk_level'] == "Low"

def test_heuristic_weather_factors():
    # User highly sensitive to weather
    priors = {
        'baseline_risk': 0.1,
        'weather_sensitivity': 1.0, # Max sensitivity
        'sleep_sensitivity': 0.5,
        'strain_sensitivity': 0.5
    }
    predictor = HeuristicPredictor(user_priors=priors)
    
    # 1. Pressure Drop Only (-10hPa = 1.0 score)
    # Contribution = 1.0 * Sen(1.0) * Scale(0.5) = 0.5
    # Total = 0.1 + 0.5 = 0.6
    res_pressure = predictor.predict({'pressure_change': -10.0})
    assert res_pressure['probability'] == 0.6 
    
    # 2. Rain Impact (>0.5mm adds +0.3 score)
    # Contribution = (0.0 + 0.3) * 1.0 * 0.5 = 0.15
    # Total = 0.1 + 0.15 = 0.25
    res_rain = predictor.predict({'pressure_change': 0.0, 'prcp': 1.0})
    assert res_rain['probability'] == 0.25
    
    # 3. Humidity Impact (>70% adds +0.2 score)
    # Contribution = 0.2 * 0.5 = 0.1
    # Total = 0.1 + 0.1 = 0.2
    res_hum = predictor.predict({'average_humidity': 80})
    assert res_hum['probability'] == 0.2

def test_sleep_and_strain():
    priors = {'baseline_risk': 0.1, 'sleep_sensitivity': 1.0, 'strain_sensitivity': 1.0, 'weather_sensitivity': 0.5}
    predictor = HeuristicPredictor(priors)
    
    # Sleep Debt 4 hours = 1.0 score
    # Contrib = 1.0 * 1.0 * 0.3 = 0.3
    # Total = 0.1 + 0.3 = 0.4
    res_sleep = predictor.predict({}, sleep_data=4.0)
    assert res_sleep['probability'] == 0.4
    
    # Strain 10/10 = 1.0 score
    # Contrib = 1.0 * 1.0 * 0.3 = 0.3
    # Total = 0.1 + 0.3 = 0.4
    res_strain = predictor.predict({}, strain_data=10.0)
    assert res_strain['probability'] == 0.4

def test_cluster_logic_scaling():
    # Rare User (Base 0.1)
    # Cluster Boost = Base(0.1) * 0.8 = 0.08
    pred_rare = HeuristicPredictor({'baseline_risk': 0.1})
    res_rare = pred_rare.predict({}, yesterday_pain=5.0)
    assert round(res_rare['probability'], 2) == 0.18
    
    # Chronic User (Base 0.5)
    # Cluster Boost = Base(0.5) * 0.8 = 0.4
    # Total = 0.5 + 0.4 = 0.9
    pred_chronic = HeuristicPredictor({'baseline_risk': 0.5})
    res_chronic = pred_chronic.predict({}, yesterday_pain=5.0)
    assert res_chronic['probability'] == 0.9
    assert res_chronic['risk_level'] == "High"

def test_heuristic_caps():
    predictor = HeuristicPredictor()
    # Extreme inputs should not exceed 1.0
    result = predictor.predict({'pressure_change': 1000.0}, sleep_data=100.0, strain_data=100.0, yesterday_pain=10.0)
    assert result['probability'] <= 1.0
    assert result['probability'] >= 0.0
