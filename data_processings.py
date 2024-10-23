from utils import GOOD_METRICS, INVERSE_METRICS

def compare_metrics(home_team_stats, away_team_stats):
    better_metrics_home = 0
    better_metrics_away = 0
    for stat in home_team_stats:
        if stat in away_team_stats:
            home_value = home_team_stats[stat]
            away_value = away_team_stats[stat]
            if stat in GOOD_METRICS:
                # For good metrics, higher is better
                if home_value > away_value:
                    better_metrics_home += 1
                elif away_value > home_value:
                    better_metrics_away += 1
            elif stat in INVERSE_METRICS:
                # For inverse metrics, lower is better
                if home_value < away_value:
                    better_metrics_home += 1
                elif away_value < home_value:
                    better_metrics_away += 1
    return better_metrics_home, better_metrics_away

def calculate_team_score(win_prob, implied_prob, season_win_pct, team_rank, metrics_better, total_metrics=15):
    metric_advantage = (metrics_better - (total_metrics - metrics_better)) / total_metrics
    score = (0.35 * metric_advantage) + (0.25 * win_prob) + (0.15 * (7 - team_rank)/6) + \
            (0.15 * season_win_pct) + (0.10 * implied_prob)
    return score

def prepare_matchup_data(date_today, home_team, away_team, home_rank, away_rank, home_odds, away_odds,
                         home_adjusted_odds, away_adjusted_odds, win_prob, edge_home, edge_away,
                         bet_size_home, bet_size_away, better_metrics_home, better_metrics_away,
                         implied_prob_home, implied_prob_away, home_win_pct, away_win_pct,
                         home_pythag, away_pythag, pythag_diff):
    home_score = calculate_team_score(1 - win_prob, implied_prob_home, home_win_pct, home_rank, better_metrics_home)
    away_score = calculate_team_score(win_prob, implied_prob_away, away_win_pct, away_rank, better_metrics_away)
    
    return {
        'Date': date_today,
        'Home Team': home_team,
        'Away Team': away_team,
        'Home Rank': home_rank,
        'Away Rank': away_rank,
        'Home Odds': home_odds,
        'Away Odds': away_odds,
        'Home Adjusted Odds': home_adjusted_odds,
        'Away Adjusted Odds': away_adjusted_odds,
        'Home Win Probability %': (1 - win_prob) * 100,
        'Away Win Probability %': win_prob * 100,
        'Home Edge': edge_home,
        'Away Edge': edge_away,
        'Home Kelly Bet Size': bet_size_home if bet_size_home is not None else 0,
        'Away Kelly Bet Size': bet_size_away if bet_size_away is not None else 0,
        'Home Metrics Better': better_metrics_home,
        'Away Metrics Better': better_metrics_away,
        'Home Implied Win %': implied_prob_home * 100,
        'Away Implied Win %': implied_prob_away * 100,
        'Home Season Win %': home_win_pct * 100 if home_win_pct is not None else None,
        'Away Season Win %': away_win_pct * 100 if away_win_pct is not None else None,
        'Home Score': home_score,
        'Away Score': away_score,
        'Home Pythagorean Win %': home_pythag * 100,
        'Away Pythagorean Win %': away_pythag * 100,
        'Pythagorean Win % Difference': pythag_diff * 100
    }

def print_results(home_team, away_team, win_prob, home_win_pct, away_win_pct, home_rank, away_rank,
                  home_odds, away_odds, implied_prob_home, implied_prob_away, home_adjusted_odds,
                  away_adjusted_odds, edge_home, edge_away, home_score, away_score,
                  home_pythag, away_pythag, pythag_diff):
    print(f"\n{home_team} (Home) vs {away_team} (Away):")
    print(f"Win Probability for {away_team}: {win_prob:.2%}")
    print(f"Win Probability for {home_team}: {1 - win_prob:.2%}")
    
    if home_win_pct is not None:
        print(f"{home_team} Current Season Win%: {home_win_pct:.3f}")
    if away_win_pct is not None:
        print(f"{away_team} Current Season Win%: {away_win_pct:.3f}")
    
    print(f"\n{home_team} Rank: {home_rank}")
    print(f"{away_team} Rank: {away_rank}")
    
    print(f"\nOdds and Edge Calculation:")
    print(f"{home_team} (Home):")
    print(f"  Original odds: {home_odds}")
    print(f"  Implied probability: {implied_prob_home:.2%}")
    print(f"  Adjusted odds: {home_adjusted_odds:.2f}")
    print(f"  Edge: {edge_home:.2f}%")
    
    print(f"\n{away_team} (Away):")
    print(f"  Original odds: {away_odds}")
    print(f"  Implied probability: {implied_prob_away:.2%}")
    print(f"  Adjusted odds: {away_adjusted_odds:.2f}")
    print(f"  Edge: {edge_away:.2f}%")

    print(f"\nTeam Scores:")
    print(f"{home_team} Score: {home_score:.4f}")
    print(f"{away_team} Score: {away_score:.4f}")

    print(f"\nPythagorean Winning Percentage:")
    print(f"{home_team} Pythagorean Win%: {home_pythag:.4f}")
    print(f"{away_team} Pythagorean Win%: {away_pythag:.4f}")
    print(f"Pythagorean Win% Difference ({home_team} - {away_team}): {pythag_diff:.4f}")

def print_bet_suggestions(home_team, away_team, bet_size_home, bet_size_away):
    if bet_size_home is not None:
        print(f"  Suggested Kelly Criterion bet size for {home_team}: ${bet_size_home:.2f}")
    else:
        print(f"  No bet suggested for {home_team} (Edge <= 1%)")
    
    if bet_size_away is not None:
        print(f"  Suggested Kelly Criterion bet size for {away_team}: ${bet_size_away:.2f}")
    else:
        print(f"  No bet suggested for {away_team} (Edge <= 1%)")

def print_team_stats(home_team, away_team, home_team_stats, away_team_stats, better_metrics_home, better_metrics_away):
    print(f"\nTeam Stats Comparison:")
    for team, stats in zip([home_team, away_team], [home_team_stats, away_team_stats]):
        print(f"{team}:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    
    print(f"\n{home_team} is better in {better_metrics_home} metrics.")
    print(f"{away_team} is better in {better_metrics_away} metrics.")