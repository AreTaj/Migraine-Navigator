
def calculate_cumulative_risk(hourly_risks):
    """
    Calculates the probability of at least one event assuming independent hourly risks.
    P(Day) = 1 - Product(1 - P(hour))
    """
    # Convert percentages to decimals
    probs = [p / 100.0 for p in hourly_risks]
    
    # Calculate probability of NO event
    prob_none = 1.0
    for p in probs:
        prob_none *= (1 - p)
    
    # Probability of AT LEAST ONE event
    prob_at_least_one = 1 - prob_none
    
    return prob_at_least_one * 100

# Hypothetical hourly curve from user's screenshot
# Peak is ~42%. Lows are ~15%.
hours = [
    38, 36, 35, 15, 20, 35, 25, 15, 14, 13, # PM to AM
    15, 18, 14, 20, 18, 18, 20, 20, 30, 40, 
    42, 38, 30, 25 
]

daily_cumulative = calculate_cumulative_risk(hours)
print(f"Hourly Risks Peak: {max(hours)}%")
print(f"Cumulative Daily Risk: {daily_cumulative:.2f}%")
