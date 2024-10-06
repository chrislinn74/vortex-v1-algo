import math

def original_method(team1_stats, team2_stats):
    # Updated metrics with RBI and LOB%
    metrics = {
        'run_differential': 0.8884, 'OPS': 0.8321, 'SLG': 0.7997, 'OBP': 0.7663,
        'ERA+': 0.7644, 'XBH': 0.7492, 'LOB%': 0.718, 'RAR': 0.6902, 'Hits': 0.687,
        'ISO': 0.6832, 'ERA': 0.6446, 'FIP': 0.6393, 'WHIP': 0.6176, 'RBI': 0.575
    }

    # Apply exponential weighting to the R-squared values
    power = 2  # You can adjust the power to control the degree of weighting
    transformed_metrics = {k: v ** power for k, v in metrics.items()}

    # Normalize the transformed metrics so the weights sum to 1
    total_transformed = sum(transformed_metrics.values())
    normalized_metrics = {k: v / total_transformed for k, v in transformed_metrics.items()}

    # List of inverse metrics where lower values are better
    inverse_metrics = ['ERA', 'FIP', 'WHIP']

    # Initialize team1 and team2 scores
    team1_score = 0
    team2_score = 0

    # Iterate over each metric and calculate its contribution for both teams
    for metric, weight in sorted(normalized_metrics.items(), key=lambda x: x[1], reverse=True):
        if metric not in team1_stats or metric not in team2_stats:
            continue  # Skip this metric if it's missing from either team's stats

        team1_value = team1_stats[metric]
        team2_value = team2_stats[metric]

        # Handle cases where both values are zero
        if team1_value == 0 and team2_value == 0:
            team1_metric_value = 0.5
            team2_metric_value = 0.5
        elif metric in ['run_differential', 'XBH', 'Hits', 'RBI']:
            # For metrics that can be negative or zero, shift the values to make them positive
            min_value = min(team1_value, team2_value)
            team1_shifted_value = team1_value - min_value + 1  # Add 1 to avoid division by zero
            team2_shifted_value = team2_value - min_value + 1
            total_shifted_value = team1_shifted_value + team2_shifted_value

            team1_metric_value = team1_shifted_value / total_shifted_value
            team2_metric_value = team2_shifted_value / total_shifted_value
        elif metric in inverse_metrics:
            # For inverse metrics, where lower values are better
            total = team1_value + team2_value
            if total == 0:
                team1_metric_value = 0.5
                team2_metric_value = 0.5
            else:
                team1_metric_value = 1 - (team1_value / total)
                team2_metric_value = 1 - (team2_value / total)
        else:
            # For positive metrics, where higher values are better
            total = team1_value + team2_value
            if total == 0:
                team1_metric_value = 0.5
                team2_metric_value = 0.5
            else:
                team1_metric_value = team1_value / total
                team2_metric_value = team2_value / total

        # Add weighted contributions to the team scores
        team1_contribution = weight * team1_metric_value
        team2_contribution = weight * team2_metric_value

        # Accumulate the scores for each team
        team1_score += team1_contribution
        team2_score += team2_contribution

    # Clamp the win probability between 0.01 and 0.99 for both teams
    total_score = team1_score + team2_score
    if total_score == 0:
        team1_win_prob = 0.5
    else:
        team1_win_prob = max(0.01, min(0.99, team1_score / total_score))
    
    return team1_win_prob