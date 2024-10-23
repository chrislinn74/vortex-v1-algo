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
import time
import io

# Streamlit imports
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Set the page config before any other Streamlit commands
st.set_page_config(layout="wide")

# Hardcoded values
bankroll = 41
max_bet_percentage = 25
max_edge = 1.3

# Hardcoded chart size in pixels
chart_width = 500  # Width in pixels
chart_height = 500  # Height in pixels

# Styling options for components
component_style = """
<style>
/* Dark Theme Styles */

/* Main container */
.stApp {
    background-color: #121212;
    color: #FFFFFF;
    padding: 20px;
}

/* Sidebar */
.stSidebar {
    background-color: #1E1E1E;
    color: #FFFFFF;
}

.stSidebar .stButton > button {
    background-color: #BB86FC;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    transition: background-color 0.3s ease;
}

.stSidebar .stButton > button:hover {
    background-color: #9F6BFF;
    color: #FFFFFF;
}

.stSidebar input {
    background-color: #2A2A2A;
    color: #FFFFFF;
    border: 1px solid #555555;
    border-radius: 5px;
}

/* Style for cards */
.card {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
}

/* Style for headers */
.card h2, .card h3, .card h4, .card h5, .card h6 {
    color: #FFFFFF;
    margin-top: 0;
}

/* Text color */
body, .markdown-text-container, .stMarkdown, .css-1cpxqw2, .stTextInput, .stNumberInput {
    color: #FFFFFF;
    background-color: #121212;
}

/* Style for progress bars */
.stProgress > div > div > div > div {
    background-color: #BB86FC;
}

/* Style for metrics */
.stMetric {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 10px;
    padding: 10px;
    color: #FFFFFF;
}

/* Style for dataframes */
.stDataFrame {
    background-color: #1E1E1E;
    color: #FFFFFF;
}

/* Adjust scrollbar colors */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #1E1E1E;
}

::-webkit-scrollbar-thumb {
    background: #333333;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555555;
}

/* Adjust input fields */
.stTextInput input, .stNumberInput input {
    background-color: #2A2A2A;
    color: #FFFFFF;
    border: 1px solid #555555;
    border-radius: 5px;
}

.stTextInput label, .stNumberInput label {
    color: #FFFFFF;
}

/* Button style */
.stButton > button {
    background-color: #BB86FC;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    transition: background-color 0.3s ease;
}

.stButton > button:hover {
    background-color: #9F6BFF;
    color: #FFFFFF;
}

/* Table styles */
.stDataFrame {
    background-color: #1E1E1E;
    color: #FFFFFF;
}

/* Adjust headers */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF;
}

/* Adjust code blocks */
code {
    background-color: #2A2A2A;
    color: #FFFFFF;
}
</style>
"""

# Inject the custom CSS styles
st.markdown(component_style, unsafe_allow_html=True)

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

    # Adjust font size based on chart size
    base_font_size = 10
    font_size = max(base_font_size * (chart_width / 500), 8)

    # Calculate figsize in inches (matplotlib uses inches)
    dpi = 100  # Dots per inch
    fig_width = chart_width / dpi
    fig_height = chart_height / dpi

    # Plot data
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, home_normalized, linewidth=2, linestyle='solid', label=home_team, color='#BB86FC')
    ax.fill(angles, home_normalized, alpha=0.25, color='#BB86FC')

    ax.plot(angles, away_normalized, linewidth=2, linestyle='solid', label=away_team, color='#03DAC6')
    ax.fill(angles, away_normalized, alpha=0.25, color='#03DAC6')

    # Add labels
    ax.set_facecolor('#121212')
    ax.tick_params(colors='#FFFFFF')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=font_size, color='#FFFFFF')
    ax.set_yticks([])
    ax.spines['polar'].set_color('#FFFFFF')
    ax.grid(color='#FFFFFF')
    legend = ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.setp(legend.get_texts(), color='#FFFFFF')
    fig.patch.set_facecolor('#121212')  # Set the figure background to match the app background

    # Save the figure to a BytesIO buffer and display it using st.image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=dpi)
    plt.close(fig)
    st.image(buf, width=chart_width, use_column_width=False)

# Function to update metrics table
def update_metrics_table(home_team, away_team, home_stats, away_stats,
                         home_win_pct, away_win_pct, home_rank, away_rank,
                         home_odds, away_odds, implied_prob_home, implied_prob_away,
                         home_adjusted_odds, away_adjusted_odds,
                         home_pythag, away_pythag, pythag_diff, win_prob):
    metric_names = [
        "Win Probability", "Current Season Win%", "Team Rank", "Moneyline Odds",
        "Implied Probability", "Adjusted Odds", "Pythagorean Win%", "Pythagorean Win% Difference"
    ]

    home_values = [
        (1 - win_prob), home_win_pct, home_rank, home_odds,
        implied_prob_home, home_adjusted_odds, home_pythag, pythag_diff
    ]

    away_values = [
        win_prob, away_win_pct, away_rank, away_odds,
        implied_prob_away, away_adjusted_odds, away_pythag, None
    ]

    # Add individual metrics
    metric_list = list(set(GOOD_METRICS + INVERSE_METRICS))

    for metric in metric_list:
        metric_names.append(metric)
        home_values.append(home_stats.get(metric, 0))
        away_values.append(away_stats.get(metric, 0))

    # Create DataFrame with metric names in the middle and team values on sides
    data = {
        home_team: home_values,
        'Metric': metric_names,
        away_team: away_values
    }
    df = pd.DataFrame(data)
    df = df[['Metric', home_team, away_team]]  # Reorder columns

    # Style the dataframe
    styled_df = df.style.set_properties(**{
        'background-color': '#1E1E1E',
        'color': '#FFFFFF',
        'border-color': '#333333',
        'text-align': 'center'
    }).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#2A2A2A'), ('color', '#FFFFFF'), ('border-color', '#333333'), ('text-align', 'center')]}
    ]).format(precision=2)

    st.write(styled_df.to_html(), unsafe_allow_html=True)

# Main function
def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
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
        status_text = st.empty()
        with st.spinner('Processing...'):
            # Capture terminal output
            buffer = io.StringIO()
            sys.stdout = buffer  # Redirect stdout to buffer
            try:
                year = datetime.now().year
                date_today = datetime.now().strftime('%Y-%m-%d')

                # Display 'Pulling game data'
                status_text.text('Pulling game data...')
                time.sleep(1)

                # Validate inputs
                try:
                    home_odds = float(home_odds_text)
                    away_odds = float(away_odds_text)
                except ValueError:
                    st.error("Please enter valid numeric odds.")
                    status_text.empty()
                    return

                if not all([home_team, away_team, pitcher_home, pitcher_away]):
                    st.error("Please fill in all fields.")
                    status_text.empty()
                    return

                try:
                    home_team_stats, used_pitcher_stats_home = get_team_stats(home_team, year, pitcher_home)
                    away_team_stats, used_pitcher_stats_away = get_team_stats(away_team, year, pitcher_away)
                except ValueError as e:
                    st.error(f"Data Error: {e}")
                    status_text.empty()
                    return

                # Display 'Processing data'
                status_text.text('Processing data...')
                time.sleep(1)

                # Win probability calculation
                win_prob = original_method(away_team_stats, home_team_stats)

                # Display 'Running data through Vortex algorithm'
                status_text.text('Running data through Vortex algorithm...')
                time.sleep(1)

                # Implied probabilities from odds
                implied_prob_home = 1 / american_to_decimal(home_odds)
                implied_prob_away = 1 / american_to_decimal(away_odds)

                # Adjusted odds
                home_adjusted_odds = calculate_adjusted_odds(home_odds, 1 - win_prob, implied_prob_home)
                away_adjusted_odds = calculate_adjusted_odds(away_odds, win_prob, implied_prob_away)

                # Current season win percentages
                home_win_pct = get_team_win_percentage(home_team, year)
                away_win_pct = get_team_win_percentage(away_team, year)

                # Get team rankings
                home_rank = get_team_rank(home_team, year)
                away_rank = get_team_rank(away_team, year)

                # Metrics comparison
                better_metrics_home, better_metrics_away = compare_metrics(home_team_stats, away_team_stats)

                # Calculate Pythagorean Winning Percentage
                home_pythag = calculate_pythagorean_winning_percentage(
                    home_team_stats['RunsScored'], home_team_stats['RunsAllowed']
                )
                away_pythag = calculate_pythagorean_winning_percentage(
                    away_team_stats['RunsScored'], away_team_stats['RunsAllowed']
                )
                pythag_diff = home_pythag - away_pythag

                # Display results
                display_results(
                    better_metrics_home, better_metrics_away, home_team, away_team,
                    win_prob, home_win_pct, away_win_pct, home_team_stats, away_team_stats,
                    home_odds, away_odds, implied_prob_home, implied_prob_away,
                    home_adjusted_odds, away_adjusted_odds,
                    home_rank, away_rank, home_pythag, away_pythag, pythag_diff
                )
            finally:
                sys.stdout = sys.__stdout__  # Reset stdout

            status_text.empty()
            st.success("Algorithm run successfully!")

        # Display terminal output in sidebar
        terminal_output = buffer.getvalue()
        st.sidebar.subheader("Terminal Output")
        st.sidebar.text(terminal_output)

    st.markdown('</div>', unsafe_allow_html=True)

def display_results(
    better_metrics_home, better_metrics_away, home_team, away_team,
    win_prob, home_win_pct, away_win_pct, home_team_stats, away_team_stats,
    home_odds, away_odds, implied_prob_home, implied_prob_away,
    home_adjusted_odds, away_adjusted_odds,
    home_rank, away_rank, home_pythag, away_pythag, pythag_diff
):
    st.header("Matchup Analysis")

    # Create columns for home and away teams
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{home_team}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>Win Probability: {(1 - win_prob) * 100:.2f}%</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:24px; text-align: center; color:#BB86FC;'>Better Metrics:<br>{better_metrics_home}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{away_team}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>Win Probability: {win_prob * 100:.2f}%</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:24px; text-align: center; color:#03DAC6;'>Better Metrics:<br>{better_metrics_away}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Radar Chart
    st.subheader("Metrics Comparison Radar Chart")
    plot_radar_chart(home_team, away_team, home_team_stats, away_team_stats)

    # Metrics Table
    st.subheader("Detailed Metrics")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    update_metrics_table(
        home_team, away_team, home_team_stats, away_team_stats,
        home_win_pct, away_win_pct, home_rank, away_rank,
        home_odds, away_odds, implied_prob_home, implied_prob_away,
        home_adjusted_odds, away_adjusted_odds,
        home_pythag, away_pythag, pythag_diff, win_prob
    )
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
