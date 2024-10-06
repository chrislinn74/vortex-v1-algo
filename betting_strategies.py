def calculate_bet_size(edge, max_edge, max_bet_percentage, bankroll):
    """
    Calculate the suggested bet size based on the edge, max edge, and bankroll.
    
    Args:
    edge (float): The calculated edge as a percentage.
    max_edge (float): The maximum allowable edge.
    max_bet_percentage (float): The maximum bet size as a percentage of the bankroll.
    bankroll (float): The current bankroll.
    
    Returns:
    float: The suggested bet size in dollars, or None if the edge is 1% or less.
    """
    if edge <= 1.00:  # No bet if edge is 1.00% or less
        return None
    
    # Calculate the ratio of the team's edge to the max edge, subtracting 1 from both
    edge_ratio = (edge - 1) / (max_edge - 1)
    
    # Calculate the maximum bet size
    max_bet_size = (max_bet_percentage / 100) * bankroll
    
    # Calculate the suggested bet size
    suggested_bet = edge_ratio * max_bet_size
    
    return suggested_bet

def suggested_bet_size(edge, max_edge, max_bet_percentage, bankroll):
    """
    Suggest a bet size based on the edge, max edge, and bankroll.
    
    Args:
    edge (float): The calculated edge as a percentage.
    max_edge (float): The maximum allowable edge.
    max_bet_percentage (float): The maximum bet size as a percentage of the bankroll.
    bankroll (float): The current bankroll.
    
    Returns:
    float: The suggested bet size in dollars, or None if the edge is 1% or less.
    """
    return calculate_bet_size(edge, max_edge, max_bet_percentage, bankroll)