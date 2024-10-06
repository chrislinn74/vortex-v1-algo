import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QWidget, QHBoxLayout, QProgressBar, QGridLayout, QSpacerItem, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from data_collection import get_team_stats, get_head_to_head
from prediction_models import original_method
from odds_calculations import american_to_decimal, calculate_adjusted_odds, calculate_edge
from betting_strategies import suggested_bet_size
from datetime import datetime
import pybaseball as pb

class MLBAIPredictor(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.setWindowTitle("MLB AI Predictor")
        self.setGeometry(100, 100, 1000, 800)

        # Set dark background color
        self.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")

        # Main Layout
        self.central_widget = QWidget()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)  # Add padding
        self.scroll.setWidget(self.scroll_content)

        self.setCentralWidget(self.scroll)

        # Fonts
        label_font = QFont("Arial", 14, QFont.Bold)
        input_font = QFont("Arial", 12)

        # Input Fields Layout
        self.input_layout = QGridLayout()
        self.input_layout.setVerticalSpacing(10)

        # Team 1 Input
        self.team1_label = QLabel("Team 1:")
        self.team1_label.setFont(label_font)
        self.team1_input = QLineEdit()
        self.team1_input.setFont(input_font)
        self.team1_input.setStyleSheet("border-radius: 5px; padding: 5px; background-color: #333333; color: white;")

        # Team 2 Input
        self.team2_label = QLabel("Team 2:")
        self.team2_label.setFont(label_font)
        self.team2_input = QLineEdit()
        self.team2_input.setFont(input_font)
        self.team2_input.setStyleSheet("border-radius: 5px; padding: 5px; background-color: #333333; color: white;")

        # Pitcher 1 Input
        self.pitcher1_label = QLabel("Pitcher 1:")
        self.pitcher1_label.setFont(label_font)
        self.pitcher1_input = QLineEdit()
        self.pitcher1_input.setFont(input_font)
        self.pitcher1_input.setStyleSheet("border-radius: 5px; padding: 5px; background-color: #333333; color: white;")

        # Pitcher 2 Input
        self.pitcher2_label = QLabel("Pitcher 2:")
        self.pitcher2_label.setFont(label_font)
        self.pitcher2_input = QLineEdit()
        self.pitcher2_input.setFont(input_font)
        self.pitcher2_input.setStyleSheet("border-radius: 5px; padding: 5px; background-color: #333333; color: white;")

        # Team 1 Odds Input
        self.team1_odds_label = QLabel("Team 1 Odds:")
        self.team1_odds_label.setFont(label_font)
        self.team1_odds_input = QLineEdit()
        self.team1_odds_input.setFont(input_font)
        self.team1_odds_input.setStyleSheet("border-radius: 5px; padding: 5px; background-color: #333333; color: white;")

        # Team 2 Odds Input
        self.team2_odds_label = QLabel("Team 2 Odds:")
        self.team2_odds_label.setFont(label_font)
        self.team2_odds_input = QLineEdit()
        self.team2_odds_input.setFont(input_font)
        self.team2_odds_input.setStyleSheet("border-radius: 5px; padding: 5px; background-color: #333333; color: white;")

        # Predict Button
        self.predict_button = QPushButton("Run Algorithm")
        self.predict_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.predict_button.setStyleSheet("background-color: #6426fd; color: white; border-radius: 5px; padding: 10px;")
        self.predict_button.clicked.connect(self.run_algorithm)
        self.predict_button.setFixedWidth(200)  # Set a fixed width for the button

        # Adding widgets to the grid
        self.input_layout.addWidget(self.team1_label, 0, 0)
        self.input_layout.addWidget(self.team1_input, 0, 1)
        self.input_layout.addWidget(self.team2_label, 1, 0)
        self.input_layout.addWidget(self.team2_input, 1, 1)
        self.input_layout.addWidget(self.pitcher1_label, 2, 0)
        self.input_layout.addWidget(self.pitcher1_input, 2, 1)
        self.input_layout.addWidget(self.pitcher2_label, 3, 0)
        self.input_layout.addWidget(self.pitcher2_input, 3, 1)
        self.input_layout.addWidget(self.team1_odds_label, 4, 0)
        self.input_layout.addWidget(self.team1_odds_input, 4, 1)
        self.input_layout.addWidget(self.team2_odds_label, 5, 0)
        self.input_layout.addWidget(self.team2_odds_input, 5, 1)
        self.input_layout.addWidget(self.predict_button, 6, 0, 1, 2, alignment=Qt.AlignCenter)

        self.scroll_layout.addLayout(self.input_layout)

        # Spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(spacer)

        # Result area
        self.result_area = QVBoxLayout()
        self.scroll_layout.addLayout(self.result_area)

        # Team abbreviation to full name mapping
        self.TEAM_ABBR_TO_NAME = {
            'ARI': 'Arizona Diamondbacks', 'ATL': 'Atlanta Braves', 'BAL': 'Baltimore Orioles',
            'BOS': 'Boston Red Sox', 'CHC': 'Chicago Cubs', 'CHW': 'Chicago White Sox',
            'CIN': 'Cincinnati Reds', 'CLE': 'Cleveland Guardians', 'COL': 'Colorado Rockies',
            'DET': 'Detroit Tigers', 'HOU': 'Houston Astros', 'KCR': 'Kansas City Royals',
            'LAA': 'Los Angeles Angels', 'LAD': 'Los Angeles Dodgers', 'MIA': 'Miami Marlins',
            'MIL': 'Milwaukee Brewers', 'MIN': 'Minnesota Twins', 'NYM': 'New York Mets',
            'NYY': 'New York Yankees', 'OAK': 'Oakland Athletics', 'PHI': 'Philadelphia Phillies',
            'PIT': 'Pittsburgh Pirates', 'SDP': 'San Diego Padres', 'SFG': 'San Francisco Giants',
            'SEA': 'Seattle Mariners', 'STL': 'St. Louis Cardinals', 'TBR': 'Tampa Bay Rays',
            'TEX': 'Texas Rangers', 'TOR': 'Toronto Blue Jays', 'WSN': 'Washington Nationals'
        }

        # Padding settings (in pixels)
        self.padding = {
            'match_result': 10,
            'win_percentage': 10,
            'win_probability': 10,
            'head_to_head': 10,
            'odds_and_edge': 10,
            'metrics_summary': 10,
            'individual_metrics': 10
        }

    def run_algorithm(self):
        # Clear previous results
        while self.result_area.count():
            widget = self.result_area.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        year = datetime.now().year

        team1 = self.team1_input.text()
        team2 = self.team2_input.text()
        pitcher1 = self.pitcher1_input.text()
        pitcher2 = self.pitcher2_input.text()
        team1_odds = float(self.team1_odds_input.text())
        team2_odds = float(self.team2_odds_input.text())

        try:
            team1_stats, used_pitcher_stats1 = get_team_stats(team1, year, pitcher1)
            team2_stats, used_pitcher_stats2 = get_team_stats(team2, year, pitcher2)
        except ValueError as e:
            self.display_error(f"Error: {e}\nUsing previous year's data.")
            year -= 1
            try:
                team1_stats, used_pitcher_stats1 = get_team_stats(team1, year, pitcher1)
                team2_stats, used_pitcher_stats2 = get_team_stats(team2, year, pitcher2)
            except ValueError as e:
                self.display_error(f"Error: {e}\nUnable to retrieve team stats.")
                return

        win_prob = original_method(team1_stats, team2_stats)

        implied_prob_team1 = 1 / american_to_decimal(team1_odds)
        implied_prob_team2 = 1 / american_to_decimal(team2_odds)

        team1_adjusted_odds = calculate_adjusted_odds(team1_odds, win_prob, implied_prob_team1)
        team2_adjusted_odds = calculate_adjusted_odds(team2_odds, 1 - win_prob, implied_prob_team2)

        edge_team1 = calculate_edge(team1_adjusted_odds, team1_odds)
        edge_team2 = calculate_edge(team2_adjusted_odds, team2_odds)

        h2h_wins, h2h_games = get_head_to_head(team1, team2, year)

        # Fetch current season Win% for both teams
        team1_win_pct = self.get_team_win_percentage(team1, year)
        team2_win_pct = self.get_team_win_percentage(team2, year)

        self.display_results(team1, team2, win_prob, team1_stats, team2_stats, h2h_wins, h2h_games, 
                             team1_win_pct, team2_win_pct, team1_adjusted_odds, team2_adjusted_odds, 
                             edge_team1, edge_team2)

    def get_team_win_percentage(self, team, year):
        try:
            standings_list = pb.standings(year)
            # Combine all DataFrames in the list into a single DataFrame
            standings = pd.concat(standings_list)
            
            # Convert team abbreviation to full name
            team_name = self.TEAM_ABBR_TO_NAME.get(team, team)
            
            team_row = standings[standings['Tm'] == team_name]
            if not team_row.empty:
                wins = int(team_row['W'].values[0])
                losses = int(team_row['L'].values[0])
                games = wins + losses
                if games > 0:
                    win_pct = wins / games
                    print(f"{team} ({team_name}) current win%: {win_pct:.3f}")
                    return win_pct
                else:
                    print(f"{team} ({team_name}) has not played any games yet.")
                    return 0.000
            else:
                print(f"Team '{team}' ({team_name}) not found in standings.")
                print("Available teams:")
                print(standings['Tm'].tolist())
                return None
        except Exception as e:
            print(f"Error fetching win percentage: {e}")
            print("Standings data:")
            print(standings.to_string())
            import traceback
            traceback.print_exc()
            return None

    def display_results(self, team1, team2, win_prob, team1_stats, team2_stats, h2h_wins, h2h_games, 
                        team1_win_pct, team2_win_pct, team1_adjusted_odds, team2_adjusted_odds, 
                        edge_team1, edge_team2):
        # Display match result
        match_layout = QHBoxLayout()
        match_layout.setContentsMargins(self.padding['match_result'], self.padding['match_result'], 
                                        self.padding['match_result'], self.padding['match_result'])
        team1_label = QLabel(team1)
        team2_label = QLabel(team2)
        vs_label = QLabel("vs")
        team1_label.setFont(QFont("Arial", 24, QFont.Bold))
        team2_label.setFont(QFont("Arial", 24, QFont.Bold))
        vs_label.setFont(QFont("Arial", 24, QFont.Bold))
        team1_label.setStyleSheet("color: #12f37e;" if win_prob > 0.5 else "color: #eb0d48;")
        team2_label.setStyleSheet("color: #12f37e;" if win_prob <= 0.5 else "color: #eb0d48;")
        vs_label.setStyleSheet("color: #FFFFFF;")
        match_layout.addWidget(team1_label, alignment=Qt.AlignRight)
        match_layout.addWidget(vs_label, alignment=Qt.AlignCenter)
        match_layout.addWidget(team2_label, alignment=Qt.AlignLeft)
        self.result_area.addLayout(match_layout)

        # Current Season Win Percentages
        win_pct_layout = QHBoxLayout()
        win_pct_layout.setContentsMargins(self.padding['win_percentage'], self.padding['win_percentage'], 
                                          self.padding['win_percentage'], self.padding['win_percentage'])
        team1_win_pct_label = QLabel(f"Win%: {team1_win_pct:.3f}" if team1_win_pct is not None else "Win%: N/A")
        team2_win_pct_label = QLabel(f"Win%: {team2_win_pct:.3f}" if team2_win_pct is not None else "Win%: N/A")
        team1_win_pct_label.setFont(QFont("Arial", 14))
        team2_win_pct_label.setFont(QFont("Arial", 14))
        win_pct_layout.addWidget(team1_win_pct_label, alignment=Qt.AlignRight)
        win_pct_layout.addWidget(team2_win_pct_label, alignment=Qt.AlignLeft)
        self.result_area.addLayout(win_pct_layout)

        # Win Probability Progress Bar
        win_prob_layout = QHBoxLayout()
        win_prob_layout.setContentsMargins(self.padding['win_probability'], self.padding['win_probability'], 
                                           self.padding['win_probability'], self.padding['win_probability'])
        win_prob_bar = QProgressBar()
        win_prob_bar.setMaximum(100)
        win_prob_bar.setValue(int(win_prob * 100))
        win_prob_bar.setStyleSheet("QProgressBar {border-radius: 5px; background-color: #555555; text-align: center;} "
                                   "QProgressBar::chunk {background-color: #12f37e; border-radius: 5px;}")
        win_prob_team1_label = QLabel(f"{win_prob:.1%}")
        win_prob_team2_label = QLabel(f"{1-win_prob:.1%}")
        win_prob_team1_label.setFont(QFont("Arial", 16, QFont.Bold))
        win_prob_team2_label.setFont(QFont("Arial", 16, QFont.Bold))
        win_prob_team1_label.setStyleSheet("color: #12f37e;" if win_prob > 0.5 else "color: #eb0d48;")
        win_prob_team2_label.setStyleSheet("color: #12f37e;" if win_prob <= 0.5 else "color: #eb0d48;")
        win_prob_layout.addWidget(win_prob_team1_label)
        win_prob_layout.addWidget(win_prob_bar)
        win_prob_layout.addWidget(win_prob_team2_label)
        self.result_area.addLayout(win_prob_layout)

        # Head-to-Head Record
        if h2h_wins is not None and h2h_games is not None:
            h2h_layout = QHBoxLayout()
            h2h_layout.setContentsMargins(self.padding['head_to_head'], self.padding['head_to_head'], 
                                          self.padding['head_to_head'], self.padding['head_to_head'])
            h2h_label = QLabel(f"Head-to-Head Record: {team1} has won {h2h_wins} out of {h2h_games} games against {team2} this season")
            h2h_label.setFont(QFont("Arial", 14))
            h2h_label.setStyleSheet("color: #FFFFFF;")
            h2h_layout.addWidget(h2h_label, alignment=Qt.AlignCenter)
            self.result_area.addLayout(h2h_layout)

        # Display adjusted odds and edge
        odds_layout = QHBoxLayout()
        odds_layout.setContentsMargins(self.padding['odds_and_edge'], self.padding['odds_and_edge'], 
                                       self.padding['odds_and_edge'], self.padding['odds_and_edge'])
        team1_odds_label = QLabel(f"Adjusted Odds: {team1_adjusted_odds:.2f}\nEdge: {edge_team1:.2f}%")
        team2_odds_label = QLabel(f"Adjusted Odds: {team2_adjusted_odds:.2f}\nEdge: {edge_team2:.2f}%")
        team1_odds_label.setFont(QFont("Arial", 12))
        team2_odds_label.setFont(QFont("Arial", 12))
        odds_layout.addWidget(team1_odds_label, alignment=Qt.AlignRight)
        odds_layout.addSpacing(20)  # Add spacing between the odds labels
        odds_layout.addWidget(team2_odds_label, alignment=Qt.AlignLeft)
        self.result_area.addLayout(odds_layout)

        # Display metric comparisons
        comparison_metrics = {
            'run_differential': 'RunD.',
            'Runs': 'Runs',
            'RBI': 'RBI',
            'WAR_hitting': 'WAR Hitting',
            'WAR_pitching': 'WAR Pitching',
            'ERA': 'ERA',
            'FIP': 'FIP',
            'LOB%': 'LOB%',
            'WHIP': 'WHIP',
            'H/9': 'H/9',
            'HR/9': 'HR/9',
            'BB/K': 'BB/K',
            'wRC+': 'wRC+',
            'Hard_Contact%': 'Hard Contact%',
            'Saves': 'Saves',
            'Run_Support': 'Run Support'
        }

        team1_better_metrics = 0
        team2_better_metrics = 0

        # Display metrics summary at the top
        metrics_summary_layout = QHBoxLayout()
        metrics_summary_layout.setContentsMargins(self.padding['metrics_summary'], self.padding['metrics_summary'], 
                                                  self.padding['metrics_summary'], self.padding['metrics_summary'])
        team1_metric_label = QLabel(f"{team1} better metrics: {team1_better_metrics}")
        team2_metric_label = QLabel(f"{team2} better metrics: {team2_better_metrics}")
        team1_metric_label.setFont(QFont("Arial", 14, QFont.Bold))
        team2_metric_label.setFont(QFont("Arial", 14, QFont.Bold))
        metrics_summary_layout.addWidget(team1_metric_label, alignment=Qt.AlignRight)
        metrics_summary_layout.addWidget(team2_metric_label, alignment=Qt.AlignLeft)
        self.result_area.addLayout(metrics_summary_layout)

        for metric, metric_name in comparison_metrics.items():
            team1_value = team1_stats.get(metric, 0)
            team2_value = team2_stats.get(metric, 0)

            # Create comparison widget
            comparison_widget = QWidget()
            layout = QHBoxLayout(comparison_widget)
            layout.setContentsMargins(self.padding['individual_metrics'], self.padding['individual_metrics'], 
                                      self.padding['individual_metrics'], self.padding['individual_metrics'])

            progress_bar1 = QProgressBar()
            progress_bar2 = QProgressBar()
            progress_bar1.setMaximum(100)
            progress_bar2.setMaximum(100)
            progress_bar1.setTextVisible(False)
            progress_bar2.setTextVisible(False)

            # Calculate which team has the better metric and set colors accordingly
            if metric in ['ERA', 'FIP', 'WHIP', 'H/9', 'HR/9', 'BB/K']:  # For metrics where lower is better
                if team1_value < team2_value:
                    team1_better_metrics += 1
                    value1 = 100
                    value2 = int((team1_value / team2_value) * 100) if team2_value != 0 else 0
                    progress_bar1.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #12f37e; border-radius: 5px;}")
                    progress_bar2.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #eb0d48; border-radius: 5px;}")
                else:
                    team2_better_metrics += 1
                    value1 = int((team2_value / team1_value) * 100) if team1_value != 0 else 0
                    value2 = 100
                    progress_bar1.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #eb0d48; border-radius: 5px;}")
                    progress_bar2.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #12f37e; border-radius: 5px;}")
            else:  # For metrics where higher is better
                if team1_value > team2_value:
                    team1_better_metrics += 1
                    value1 = 100
                    value2 = int((team2_value / team1_value) * 100) if team1_value != 0 else 0
                    progress_bar1.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #12f37e; border-radius: 5px;}")
                    progress_bar2.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #eb0d48; border-radius: 5px;}")
                else:
                    team2_better_metrics += 1
                    value1 = int((team1_value / team2_value) * 100) if team2_value != 0 else 0
                    value2 = 100
                    progress_bar1.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #eb0d48; border-radius: 5px;}")
                    progress_bar2.setStyleSheet("QProgressBar {background-color: #555555; border-radius: 5px;} QProgressBar::chunk {background-color: #12f37e; border-radius: 5px;}")

            progress_bar1.setValue(value1)
            progress_bar2.setValue(value2)

            value1_label = QLabel(f"{team1_value:.2f}")
            value2_label = QLabel(f"{team2_value:.2f}")
            metric_label = QLabel(metric_name)
            
            value1_label.setFont(QFont("Arial", 10))
            value2_label.setFont(QFont("Arial", 10))
            metric_label.setFont(QFont("Arial", 10, QFont.Bold))  # Make metric name bold
            metric_label.setAlignment(Qt.AlignCenter)

            layout.addWidget(value1_label)
            layout.addWidget(progress_bar1)
            layout.addWidget(metric_label)
            layout.addWidget(progress_bar2)
            layout.addWidget(value2_label)

            self.result_area.addWidget(comparison_widget)

        # Update metrics summary
        team1_metric_label.setText(f"{team1} better metrics: {team1_better_metrics}")
        team2_metric_label.setText(f"{team2} better metrics: {team2_better_metrics}")
        team1_metric_label.setStyleSheet("color: #12f37e;" if team1_better_metrics > team2_better_metrics else "color: #eb0d48;")
        team2_metric_label.setStyleSheet("color: #12f37e;" if team2_better_metrics > team1_better_metrics else "color: #eb0d48;")

    def display_error(self, message):
        error_label = QLabel(message)
        error_label.setFont(QFont("Arial", 14))
        error_label.setStyleSheet("color: red")
        self.result_area.addWidget(error_label)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MLBAIPredictor()
    window.show()
    sys.exit(app.exec_())