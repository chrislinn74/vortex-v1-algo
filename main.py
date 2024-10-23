# main.py

import sys
from data_collection import get_team_stats, get_team_rank, get_head_to_head, calculate_pythagorean_winning_percentage
from prediction_models import original_method
from odds_calculations import american_to_decimal, calculate_adjusted_odds, calculate_edge
from utils import save_to_excel, get_team_win_percentage, GOOD_METRICS, INVERSE_METRICS  # Imported GOOD_METRICS and INVERSE_METRICS
from data_processings import compare_metrics, prepare_matchup_data, calculate_team_score
from datetime import datetime
import os

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGridLayout, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QBrush
from PyQt5.QtCore import Qt, QSize

# PyQt5 Circular Progress Bar imports
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QPen

# Matplotlib imports for embedding charts
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Hardcoded values
bankroll = 41
max_bet_percentage = 25
max_edge = 1.3
output_file = "mlb_matchup_data.xlsx"  # Excel output file name

class CircularProgress(QFrame):
    def __init__(self, value=0, max_value=17, color=QColor(0, 255, 0), parent=None):
        super().__init__(parent)
        self.value = value
        self.max_value = max_value
        self.color = color
        self.width = 250
        self.height = 250
        self.setMinimumSize(self.width, self.height)

    def setValue(self, value):
        self.value = value
        self.repaint()

    def paintEvent(self, event):
        width = self.width - 10
        height = self.height - 10
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Draw background circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(40, 40, 40, 150))
        painter.drawEllipse(5, 5, width, height)

        # Draw progress
        painter.setBrush(Qt.NoBrush)
        pen = QPen()
        pen.setColor(self.color)
        pen.setWidth(10)
        painter.setPen(pen)

        start_angle = -90 * 16
        span_angle = -int((self.value / self.max_value) * 360 * 16)
        painter.drawArc(5, 5, width, height, start_angle, span_angle)

        # Draw metric number centered in the circle
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 36, QFont.Bold))
        text = f"{self.value}"
        painter.drawText(rect, Qt.AlignCenter, text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MLB Betting Algorithm")
        self.setGeometry(100, 100, 1200, 900)
        self.initUI()

    def initUI(self):
        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Set background image
        oImage = QPixmap(os.path.join('media', 'abstract-background.png'))
        sImage = oImage.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(sImage))
        self.setPalette(palette)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Center the content

        # Input fields
        input_group = QWidget()
        input_layout = QGridLayout(input_group)
        input_layout.setHorizontalSpacing(20)
        input_layout.setVerticalSpacing(5)
        input_layout.setContentsMargins(0, 0, 0, 0)

        font = QFont("Arial", 14)

        self.home_team_input = QLineEdit()
        self.home_team_input.setPlaceholderText("e.g., NYY")
        self.home_team_input.setFont(font)
        input_layout.addWidget(QLabel("Home Team Abbreviation:"), 0, 0)
        input_layout.addWidget(self.home_team_input, 0, 1)

        self.away_team_input = QLineEdit()
        self.away_team_input.setPlaceholderText("e.g., BOS")
        self.away_team_input.setFont(font)
        input_layout.addWidget(QLabel("Away Team Abbreviation:"), 0, 2)
        input_layout.addWidget(self.away_team_input, 0, 3)

        self.pitcher_home_input = QLineEdit()
        self.pitcher_home_input.setPlaceholderText("e.g., Gerrit Cole")
        self.pitcher_home_input.setFont(font)
        input_layout.addWidget(QLabel("Home Team Starting Pitcher:"), 1, 0)
        input_layout.addWidget(self.pitcher_home_input, 1, 1)

        self.pitcher_away_input = QLineEdit()
        self.pitcher_away_input.setPlaceholderText("e.g., Chris Sale")
        self.pitcher_away_input.setFont(font)
        input_layout.addWidget(QLabel("Away Team Starting Pitcher:"), 1, 2)
        input_layout.addWidget(self.pitcher_away_input, 1, 3)

        self.home_odds_input = QLineEdit()
        self.home_odds_input.setPlaceholderText("e.g., -150")
        self.home_odds_input.setFont(font)
        input_layout.addWidget(QLabel("Home Team Moneyline Odds:"), 2, 0)
        input_layout.addWidget(self.home_odds_input, 2, 1)

        self.away_odds_input = QLineEdit()
        self.away_odds_input.setPlaceholderText("e.g., +130")
        self.away_odds_input.setFont(font)
        input_layout.addWidget(QLabel("Away Team Moneyline Odds:"), 2, 2)
        input_layout.addWidget(self.away_odds_input, 2, 3)

        # Center the input fields
        input_container = QWidget()
        input_container_layout = QHBoxLayout(input_container)
        input_container_layout.addStretch()
        input_container_layout.addWidget(input_group)
        input_container_layout.addStretch()

        # Run Algorithm Button
        self.run_button = QPushButton("Run Algorithm")
        self.run_button.setFont(QFont("Arial", 14, QFont.Bold))
        self.run_button.clicked.connect(self.run_algorithm)
        self.run_button.setFixedSize(QSize(200, 40))

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.run_button)
        button_layout.addStretch()

        main_layout.addWidget(input_container)
        main_layout.addLayout(button_layout)

        # Visual Comparisons
        comparison_group = QWidget()
        comparison_layout = QHBoxLayout(comparison_group)
        comparison_layout.setSpacing(20)
        comparison_layout.setContentsMargins(0, 0, 0, 0)

        # Home Team Widget
        home_team_widget = QWidget()
        home_team_layout = QVBoxLayout(home_team_widget)
        home_team_layout.setAlignment(Qt.AlignCenter)
        home_team_layout.setSpacing(10)

        self.home_team_label = QLabel()
        self.home_team_label.setFont(QFont("Arial", 20))
        self.home_team_label.setAlignment(Qt.AlignCenter)

        self.home_metrics_progress = CircularProgress(parent=self)

        # Progress Bar for Home Win Probability
        self.win_prob_home = QProgressBar()
        self.win_prob_home.setMaximum(100)
        self.win_prob_home.setAlignment(Qt.AlignCenter)
        self.win_prob_home.setTextVisible(True)
        self.win_prob_home.setFixedSize(QSize(250, 30))
        self.win_prob_home.setFont(QFont("Arial", 12, QFont.Bold))

        home_team_layout.addWidget(self.home_team_label)
        home_team_layout.addWidget(self.home_metrics_progress)
        home_team_layout.addWidget(self.win_prob_home)

        # Away Team Widget
        away_team_widget = QWidget()
        away_team_layout = QVBoxLayout(away_team_widget)
        away_team_layout.setAlignment(Qt.AlignCenter)
        away_team_layout.setSpacing(10)

        self.away_team_label = QLabel()
        self.away_team_label.setFont(QFont("Arial", 20))
        self.away_team_label.setAlignment(Qt.AlignCenter)

        self.away_metrics_progress = CircularProgress(parent=self)

        # Progress Bar for Away Win Probability
        self.win_prob_away = QProgressBar()
        self.win_prob_away.setMaximum(100)
        self.win_prob_away.setAlignment(Qt.AlignCenter)
        self.win_prob_away.setTextVisible(True)
        self.win_prob_away.setFixedSize(QSize(250, 30))
        self.win_prob_away.setFont(QFont("Arial", 12, QFont.Bold))

        away_team_layout.addWidget(self.away_team_label)
        away_team_layout.addWidget(self.away_metrics_progress)
        away_team_layout.addWidget(self.win_prob_away)

        # Radar Chart Canvas
        self.radar_chart_canvas = FigureCanvas(Figure(figsize=(3.5, 3.5), facecolor='none'))  # Increased size
        self.radar_chart_canvas.setFixedSize(350, 350)
        self.radar_chart_canvas.setStyleSheet("background: transparent;")
        self.radar_chart_canvas.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # Create layouts for left, center, and right
        left_layout = QVBoxLayout()
        left_layout.addWidget(home_team_widget)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.radar_chart_canvas)

        right_layout = QVBoxLayout()
        right_layout.addWidget(away_team_widget)

        # Combine layouts
        comparison_layout.addLayout(left_layout)
        comparison_layout.addLayout(center_layout)
        comparison_layout.addLayout(right_layout)

        comparison_container = QWidget()
        comparison_container_layout = QHBoxLayout(comparison_container)
        comparison_container_layout.addStretch()
        comparison_container_layout.addWidget(comparison_group)
        comparison_container_layout.addStretch()

        main_layout.addWidget(comparison_container, stretch=1)

        # Metrics Table
        self.metrics_table = QTableWidget()
        self.metrics_table.setRowCount(0)
        self.metrics_table.setColumnCount(0)
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metrics_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metrics_table.setFont(QFont("Arial", 10))  # Reduced font size
        main_layout.addWidget(self.metrics_table)

        # Apply custom styling
        self.apply_styling()

    def apply_styling(self):
        # Set the primary color to a blue-purple
        primary_color = "#6a0dad"  # Dark violet

        # Style the Run Algorithm button
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_color};
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #7a1dad;
            }}
        """)

        # Style input fields and labels
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 180);
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                background-color: rgba(60, 60, 60, 180);
                color: #ffffff;
                border: 1px solid #555555;
                text-align: center;
            }
            QTableWidget {
                background-color: rgba(45, 45, 45, 180);
                color: #ffffff;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: rgba(60, 60, 60, 180);
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
        """)

    def resizeEvent(self, event):
        # Update background image to scale with window size
        oImage = QPixmap(os.path.join('media', 'abstract-background.png'))
        sImage = oImage.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(sImage))
        self.setPalette(palette)
        super().resizeEvent(event)

    def run_algorithm(self):
        year = datetime.now().year
        date_today = datetime.now().strftime('%Y-%m-%d')

        # Retrieve input values
        home_team = self.home_team_input.text().strip()
        away_team = self.away_team_input.text().strip()
        pitcher_home = self.pitcher_home_input.text().strip()
        pitcher_away = self.pitcher_away_input.text().strip()
        home_odds_text = self.home_odds_input.text().strip()
        away_odds_text = self.away_odds_input.text().strip()

        # Validate inputs
        try:
            home_odds = float(home_odds_text)
            away_odds = float(away_odds_text)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numeric odds.")
            return

        if not all([home_team, away_team, pitcher_home, pitcher_away]):
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return

        try:
            home_team_stats, used_pitcher_stats_home = get_team_stats(home_team, year, pitcher_home)
            away_team_stats, used_pitcher_stats_away = get_team_stats(away_team, year, pitcher_away)
        except ValueError as e:
            QMessageBox.warning(self, "Data Error", f"Error: {e}")
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
        home_pythag = calculate_pythagorean_winning_percentage(home_team_stats['RunsScored'], home_team_stats['RunsAllowed'])
        away_pythag = calculate_pythagorean_winning_percentage(away_team_stats['RunsScored'], away_team_stats['RunsAllowed'])
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

        # Update the visual comparisons
        self.update_visual_comparisons(
            better_metrics_home, better_metrics_away, home_team, away_team,
            win_prob, home_win_pct, away_win_pct, home_team_stats, away_team_stats,
            home_odds, away_odds, implied_prob_home, implied_prob_away,
            home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
            home_rank, away_rank, home_pythag, away_pythag, pythag_diff
        )

    def update_visual_comparisons(self, better_metrics_home, better_metrics_away, home_team, away_team,
                                  win_prob, home_win_pct, away_win_pct, home_team_stats, away_team_stats,
                                  home_odds, away_odds, implied_prob_home, implied_prob_away,
                                  home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
                                  home_rank, away_rank, home_pythag, away_pythag, pythag_diff):
        # Update Circular Progress Bars for Metrics Comparison
        self.home_metrics_progress.setValue(better_metrics_home)
        self.away_metrics_progress.setValue(better_metrics_away)

        # Set colors based on which team has better stats
        if better_metrics_home > better_metrics_away:
            home_color = QColor(0, 255, 0)  # Green
            away_color = QColor(255, 0, 0)  # Red
        elif better_metrics_home < better_metrics_away:
            home_color = QColor(255, 0, 0)  # Red
            away_color = QColor(0, 255, 0)  # Green
        else:
            home_color = away_color = QColor(255, 165, 0)  # Orange for tie

        self.home_metrics_progress.color = home_color
        self.away_metrics_progress.color = away_color

        # Update team name labels
        self.home_team_label.setText(f"{home_team}")
        self.away_team_label.setText(f"{away_team}")

        self.home_metrics_progress.repaint()
        self.away_metrics_progress.repaint()

        # Update Win Probability Progress Bars
        home_win_prob_percent = (1 - win_prob) * 100
        away_win_prob_percent = win_prob * 100

        self.win_prob_home.setValue(int(home_win_prob_percent))
        self.win_prob_home.setFormat(f"{home_team}: {home_win_prob_percent:.1f}%")
        self.win_prob_away.setValue(int(away_win_prob_percent))
        self.win_prob_away.setFormat(f"{away_team}: {away_win_prob_percent:.1f}%")

        # Set progress bar colors based on win probability
        if home_win_prob_percent > 50:
            home_bar_style = """
            QProgressBar::chunk {
                background-color: green;
            }
            """
        else:
            home_bar_style = """
            QProgressBar::chunk {
                background-color: red;
            }
            """
        self.win_prob_home.setStyleSheet(home_bar_style)

        if away_win_prob_percent > 50:
            away_bar_style = """
            QProgressBar::chunk {
                background-color: green;
            }
            """
        else:
            away_bar_style = """
            QProgressBar::chunk {
                background-color: red;
            }
            """
        self.win_prob_away.setStyleSheet(away_bar_style)

        # Update Radar Chart
        self.plot_radar_chart(home_team, away_team, home_team_stats, away_team_stats)

        # Update Metrics Table
        self.update_metrics_table(home_team, away_team, home_team_stats, away_team_stats,
                                  home_win_pct, away_win_pct, home_rank, away_rank,
                                  home_odds, away_odds, implied_prob_home, implied_prob_away,
                                  home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
                                  home_pythag, away_pythag, pythag_diff, win_prob)

    def plot_radar_chart(self, home_team, away_team, home_stats, away_stats):
        self.radar_chart_canvas.figure.clear()
        fig = self.radar_chart_canvas.figure
        ax = fig.add_subplot(111, polar=True)
        fig.patch.set_facecolor('none')
        ax.set_facecolor('none')

        # Define the metrics to compare
        metrics = ['OPS', 'SLG', 'OBP', 'XBH', 'Hits', 'ISO', 'RAR', 'RBI', 'LOB%',
                   'RunsScored', 'ERA', 'FIP', 'WHIP', 'ERA-', 'FIP-', 'R', 'ER']
        num_metrics = len(metrics)

        # Prepare data
        home_values = [home_stats.get(metric, 0) for metric in metrics]
        away_values = [away_stats.get(metric, 0) for metric in metrics]

        # Normalize data for radar chart
        max_values = [max(abs(home), abs(away)) for home, away in zip(home_values, away_values)]
        home_normalized = [home / max_val if max_val != 0 else 0 for home, max_val in zip(home_values, max_values)]
        away_normalized = [away / max_val if max_val != 0 else 0 for away, max_val in zip(away_values, max_values)]

        # Create angles for each axis
        angles = [n / float(num_metrics) * 2 * 3.1415926 for n in range(num_metrics)]
        angles += angles[:1]  # Complete the loop

        # Append first value to complete the loop
        home_normalized += home_normalized[:1]
        away_normalized += away_normalized[:1]

        # Plot data
        ax.plot(angles, home_normalized, linewidth=2, linestyle='solid', label=home_team, color='cyan')
        ax.fill(angles, home_normalized, alpha=0.4, color='cyan')

        ax.plot(angles, away_normalized, linewidth=2, linestyle='solid', label=away_team, color='magenta')
        ax.fill(angles, away_normalized, alpha=0.4, color='magenta')

        # Add labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=9, color='white')
        ax.tick_params(axis='x', colors='white', labelsize=8)
        ax.tick_params(axis='y', colors='white')
        ax.set_yticks([])

        # Adjust the position to prevent text cut off
        fig.subplots_adjust(left=0.1, right=0.9, top=1.0, bottom=0.0)

        # Remove background grid and spines
        ax.spines['polar'].set_color('white')
        ax.grid(color='gray', linestyle='--', linewidth=0.5)

        # Move legend outside the chart
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), facecolor='none', edgecolor='white', labelcolor='white', fontsize=8)

        # Adjust layout and redraw canvas
        self.radar_chart_canvas.draw()

    def update_metrics_table(self, home_team, away_team, home_stats, away_stats,
                             home_win_pct, away_win_pct, home_rank, away_rank,
                             home_odds, away_odds, implied_prob_home, implied_prob_away,
                             home_adjusted_odds, away_adjusted_odds, edge_home, edge_away,
                             home_pythag, away_pythag, pythag_diff, win_prob):
        # Clear existing rows and columns
        self.metrics_table.clear()
        self.metrics_table.setRowCount(0)
        self.metrics_table.setColumnCount(0)

        # Define metrics to display
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

        # Set column and row counts
        self.metrics_table.setColumnCount(len(metric_names))
        self.metrics_table.setRowCount(2)

        # Set headers
        self.metrics_table.setHorizontalHeaderLabels(metric_names)
        self.metrics_table.setVerticalHeaderLabels([home_team, away_team])

        # Populate table
        for col, metric_name in enumerate(metric_names):
            # Home team data
            home_value = home_values[col]
            if isinstance(home_value, float):
                home_display = f"{home_value:.4f}"
            elif home_value is None:
                home_display = ""
            else:
                home_display = str(home_value)
            item_home = QTableWidgetItem(home_display)
            self.metrics_table.setItem(0, col, item_home)

            # Away team data
            away_value = away_values[col]
            if isinstance(away_value, float):
                away_display = f"{away_value:.4f}"
            elif away_value is None:
                away_display = ""
            else:
                away_display = str(away_value)
            item_away = QTableWidgetItem(away_display)
            self.metrics_table.setItem(1, col, item_away)

            # Color cells based on comparison
            if home_value is not None and away_value is not None and col >= 9:  # Skip first 9 general stats
                try:
                    home_num = float(home_value)
                    away_num = float(away_value)
                    metric = metric_name
                    if metric in GOOD_METRICS:
                        if home_num > away_num:
                            self.metrics_table.item(0, col).setBackground(QColor(0, 100, 0, 150))  # Dark Green
                            self.metrics_table.item(1, col).setBackground(QColor(139, 0, 0, 150))  # Dark Red
                        elif away_num > home_num:
                            self.metrics_table.item(0, col).setBackground(QColor(139, 0, 0, 150))  # Dark Red
                            self.metrics_table.item(1, col).setBackground(QColor(0, 100, 0, 150))  # Dark Green
                    elif metric in INVERSE_METRICS:
                        if home_num < away_num:
                            self.metrics_table.item(0, col).setBackground(QColor(0, 100, 0, 150))  # Dark Green
                            self.metrics_table.item(1, col).setBackground(QColor(139, 0, 0, 150))  # Dark Red
                        elif away_num < home_num:
                            self.metrics_table.item(0, col).setBackground(QColor(139, 0, 0, 150))  # Dark Red
                            self.metrics_table.item(1, col).setBackground(QColor(0, 100, 0, 150))  # Dark Green
                except ValueError:
                    pass  # Non-numeric value

        # Resize columns and rows
        self.metrics_table.resizeColumnsToContents()
        self.metrics_table.resizeRowsToContents()

    def keyPressEvent(self, event):
        # Override to prevent closing the application with Esc key
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
