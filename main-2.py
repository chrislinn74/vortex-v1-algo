# main-2.py

import sys
from data_collection import (
    get_team_stats,
    get_team_rank,
    get_head_to_head,
    calculate_pythagorean_winning_percentage,
)
from prediction_models import original_method
from odds_calculations import (
    american_to_decimal,
    calculate_adjusted_odds,
    calculate_edge,
)
from utils import (
    save_to_excel,
    get_team_win_percentage,
    GOOD_METRICS,
    INVERSE_METRICS,
)
from data_processings import (
    compare_metrics,
    prepare_matchup_data,
    calculate_team_score,
)
from datetime import datetime
import os

# Streamlit imports
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Hardcoded values
bankroll = 41
max_bet_percentage = 25
max_edge = 1.3
output_file = "mlb_matchup_data.xlsx"  # Excel output file name

# Function to plot radar chart
def plot_radar_chart(home_team, away_team, home_stats, away_stats):
    metrics = [
        'OPS', 'SLG', 'OBP', 'XBH', 'Hits', 'ISO', 'RAR', 'RBI', 'LOB%',
        'RunsScored', 'ERA', 'FIP', 'WHIP', 'ERA-', 'FIP-', 'R', 'ER'
    ]
    num_metrics = len(metrics)

    # Prepare data
    home_values = [home_stats.get(metric, 0) for metric in metrics]
    away_values = [away_stats.get(metric, 0) for metric in metrics]

    # Normalize data for radar chart
    max_values = [max(abs(home), abs(away), 1) for home, away in zip(home_values, away_values)]
    home_normalized = [home / max_val for home, max_val in zip(home_values, max_values)]
    away_normalized = [away / max_val for away, max_val in zip(away_values, max_values)]

    # Create angles for each axis
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    # Append first value to complete the loop
    home_normalized += home_normalized[:1]
    away_normalized += away_normalized[:1]

    # Plot data
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, home_normalized, linewidth=2, linestyle='solid', label=home_team, color='cyan')
    ax.fill(angles, home_normalized, alpha=0.4, color='cyan')

    ax.plot(angles, away_normalized, linewidth=2, linestyle='solid', label=away_team, color='magenta')
    ax.fill(angles, away_normalized, alpha=0.4, color='magenta')

    # Add labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=9)
    ax.set_yticks([])
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))

    st.pyplot(fig)

# Function to update metrics table
def update_metrics_table(home_team, away_team, home_stats, away_stats,
                         home_win_pct, away_win_pct, home_rank, away_rank,
                         home_odds, away_odds, implied_prob_home, implied_prob_away,
                         home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
                         home_pythag, away_pythag, pythag_diff, win_prob):
    metric_names = [
        "Win Probability", "Current Season Win%", "Team Rank", "Moneyline Odds",
        "Implied Probability", "Adjusted Odds", "Edge", "Pythagorean Win%", "Pythagorean Win% Difference"
    ]

    home_values = [
        (1 - win_prob), home_win_pct, home_rank, home_odds,
        implied_prob_home, home_adjusted_odds, edge_home, home_pythag, pythag_diff
    ]

    away_values = [
        win_prob, away_win_pct, away_rank, away_odds,
        implied_prob_away, away_adjusted_odds, edge_away, away_pythag, None  # No value for pythag_diff
    ]

    # Add individual metrics
    metric_list = list(set(GOOD_METRICS + INVERSE_METRICS))

    for metric in metric_list:
        metric_names.append(metric)
        home_values.append(home_stats.get(metric, 0))
        away_values.append(away_stats.get(metric, 0))

    # Create DataFrame
    data = {
        'Metric': metric_names,
        home_team: home_values,
        away_team: away_values
    }

    df = pd.DataFrame(data)
    st.dataframe(df.set_index('Metric'))

# Main function
def main():
    st.set_page_config(layout="wide")
    st.title("MLB Betting Algorithm")

    # Input fields
    st.sidebar.header("Input Parameters")
    home_team = st.sidebar.text_input("Home Team Abbreviation (e.g., NYY)")
    away_team = st.sidebar.text_input("Away Team Abbreviation (e.g., BOS)")
    pitcher_home = st.sidebar.text_input("Home Team Starting Pitcher (e.g., Gerrit Cole)")
    pitcher_away = st.sidebar.text_input("Away Team Starting Pitcher (e.g., Chris Sale)")
    home_odds_text = st.sidebar.text_input("Home Team Moneyline Odds (e.g., -150)")
    away_odds_text = st.sidebar.text_input("Away Team Moneyline Odds (e.g., +130)")

    if st.sidebar.button("Run Algorithm"):
        year = datetime.now().year
        date_today = datetime.now().strftime('%Y-%m-%d')

        # Validate inputs
        try:
            home_odds = float(home_odds_text)
            away_odds = float(away_odds_text)
        except ValueError:
            st.error("Please enter valid numeric odds.")
            return

        if not all([home_team, away_team, pitcher_home, pitcher_away]):
            st.error("Please fill in all fields.")
            return

        try:
            home_team_stats, used_pitcher_stats_home = get_team_stats(home_team, year, pitcher_home)
            away_team_stats, used_pitcher_stats_away = get_team_stats(away_team, year, pitcher_away)
        except ValueError as e:
            st.error(f"Data Error: {e}")
            return

        # Win probability calculation
        win_prob = original_method(away_team_stats, home_team_stats)

        # Implied probabilities from odds
        implied_prob_home = 1 / american_to_decimal(home_odds)
        implied_prob_away = 1 / american_to_decimal(away_odds)

        # Adjusted odds
        home_adjusted_odds = calculate_adjusted_odds(home_odds, 1 - win_prob, implied_prob_home)
        away_adjusted_odds = calculate_adjusted_odds(away_odds, win_prob, implied_prob_away)

        # Edge calculation
        edge_home = calculate_edge(home_adjusted_odds, home_odds)
        edge_away = calculate_edge(away_adjusted_odds, away_odds)

        # Head-to-head data
        h2h_wins, h2h_games = get_head_to_head(away_team, home_team, year)

        # Current season win percentages
        home_win_pct = get_team_win_percentage(home_team, year)
        away_win_pct = get_team_win_percentage(away_team, year)

        # Get team rankings
        home_rank = get_team_rank(home_team, year)
        away_rank = get_team_rank(away_team, year)

        # Metrics comparison
        better_metrics_home, better_metrics_away = compare_metrics(home_team_stats, away_team_stats)

        # Calculate team scores
        home_score = calculate_team_score(1 - win_prob, implied_prob_home, home_win_pct, home_rank, better_metrics_home)
        away_score = calculate_team_score(win_prob, implied_prob_away, away_win_pct, away_rank, better_metrics_away)

        # Calculate Pythagorean Winning Percentage
        home_pythag = calculate_pythagorean_winning_percentage(
            home_team_stats['RunsScored'], home_team_stats['RunsAllowed']
        )
        away_pythag = calculate_pythagorean_winning_percentage(
            away_team_stats['RunsScored'], away_team_stats['RunsAllowed']
        )
        pythag_diff = home_pythag - away_pythag

        # Prepare matchup data for saving
        matchup_data = prepare_matchup_data(
            date_today, home_team, away_team, home_rank, away_rank, home_odds, away_odds,
            home_adjusted_odds, away_adjusted_odds, win_prob, edge_home, edge_away,
            None, None, better_metrics_home, better_metrics_away,
            implied_prob_home, implied_prob_away, home_win_pct, away_win_pct,
            home_pythag, away_pythag, pythag_diff
        )

        # Save data to Excel
        save_to_excel(matchup_data, output_file)

        # Display results
        display_results(
            better_metrics_home, better_metrics_away, home_team, away_team,
            win_prob, home_win_pct, away_win_pct, home_team_stats, away_team_stats,
            home_odds, away_odds, implied_prob_home, implied_prob_away,
            home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
            home_rank, away_rank, home_pythag, away_pythag, pythag_diff
        )

def display_results(
    better_metrics_home, better_metrics_away, home_team, away_team,
    win_prob, home_win_pct, away_win_pct, home_team_stats, away_team_stats,
    home_odds, away_odds, implied_prob_home, implied_prob_away,
    home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
    home_rank, away_rank, home_pythag, away_pythag, pythag_diff
):
    st.header("Matchup Analysis")

    # Create columns for home and away teams
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"{home_team}")
        st.metric("Better Metrics", f"{better_metrics_home}")
        home_win_prob_percent = (1 - win_prob) * 100
        st.progress(int(home_win_prob_percent))
        st.write(f"Win Probability: {home_win_prob_percent:.2f}%")

    with col2:
        st.subheader(f"{away_team}")
        st.metric("Better Metrics", f"{better_metrics_away}")
        away_win_prob_percent = win_prob * 100
        st.progress(int(away_win_prob_percent))
        st.write(f"Win Probability: {away_win_prob_percent:.2f}%")

    # Radar Chart
    st.subheader("Metrics Comparison Radar Chart")
    plot_radar_chart(home_team, away_team, home_team_stats, away_team_stats)

    # Metrics Table
    st.subheader("Detailed Metrics")
    update_metrics_table(
        home_team, away_team, home_team_stats, away_team_stats,
        home_win_pct, away_win_pct, home_rank, away_rank,
        home_odds, away_odds, implied_prob_home, implied_prob_away,
        home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
        home_pythag, away_pythag, pythag_diff, win_prob
    )

if __name__ == "__main__":
    main()
