def american_to_decimal(odds):
    """
    Converts American odds to decimal odds.
    
    Args:
    odds (float): The American odds.
    
    Returns:
    float: The decimal odds.
    """
    return (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1

def decimal_to_american(decimal_odds):
    """
    Converts decimal odds to American odds.
    
    Args:
    decimal_odds (float): The decimal odds.
    
    Returns:
    float: The American odds.
    """
    return (decimal_odds - 1) * 100 if decimal_odds >= 2 else -100 / (decimal_odds - 1)

def calculate_adjusted_odds(original_odds, predicted_prob, implied_prob):
    """
    Adjusts the odds based on predicted and implied probabilities.
    
    Args:
    original_odds (float): The original American odds.
    predicted_prob (float): The predicted win probability.
    implied_prob (float): The implied probability from the odds.
    
    Returns:
    float: The adjusted odds.
    """
    adjustment_factor = max(0.01, min(predicted_prob / implied_prob, 100))  # Clamp the adjustment factor

    if original_odds > 0:
        adjusted_odds = original_odds / adjustment_factor
    else:
        adjusted_odds = original_odds * adjustment_factor

    # Clamp adjusted odds
    adjusted_odds = max(-500, min(adjusted_odds, 500))

    return adjusted_odds

def calculate_edge(adjusted_odds, original_odds):
    """
    Calculates the edge based on adjusted and original odds.
    
    Args:
    adjusted_odds (float): The adjusted odds.
    original_odds (float): The original American odds.
    
    Returns:
    float: The edge percentage.
    """
    if original_odds < 0:
        edge = (adjusted_odds / original_odds)
    else:
        edge = (original_odds / adjusted_odds)
    return edge
