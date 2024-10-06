import pybaseball as pb
import pandas as pd
import subprocess
import re

def clean_date(date_str):
    """
    Clean the date string to handle doubleheaders and ensure a standard format.
    """
    clean_date_str = re.sub(r'\(.*\)', '', date_str).strip()
    return clean_date_str

def fetch_historical_data(team, year):
    """
    Fetch historical game stats for a specific team and year.
    """
    try:
        games = pb.schedule_and_record(year, team)
        if games.empty:
            raise ValueError(f"No data found for {team} in {year}.")
        return games
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def run_main_py(team1, team2, pitcher1, pitcher2, odds_team1, odds_team2):
    """
    Run main.py with necessary inputs for a given game between team1 and team2.
    """
    try:
        result = subprocess.run(
            ["python", "main.py"],
            input=f"{team1}\n{team2}\n{pitcher1}\n{pitcher2}\n{odds_team1}\n{odds_team2}\n",
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        return output
    except Exception as e:
        return None

def calculate_profit_loss(bet_size, team_odds, outcome):
    """
    Calculate the profit or loss for a given bet based on the Kelly bet size, odds, and outcome.
    """
    if outcome == 1:  # Win
        profit = bet_size * (team_odds - 1)  # Profit based on decimal odds
    else:  # Loss
        profit = -bet_size  # The bet amount is lost
    return profit

def extract_edge_from_result(result):
    """
    Extract the edge percentage for the selected team from the output of main.py.
    """
    try:
        match = re.search(r'Edge: (-?[0-9]+(?:\.[0-9]+)?)%', result)
        if match:
            return float(match.group(1))
        return 0
    except Exception:
        return 0

def simulate_betting_strategy(games, bankroll, team, max_games):
    """
    Simulate bets on historical games by automatically running main.py.
    """
    total_bets = 0
    profitable_bets = 0
    total_profit = 0
    biggest_profit = 0
    biggest_loss = 0
    profit_history = []
    
    # Only process the first 'max_games' games
    games = games.head(max_games)

    for idx, game in games.iterrows():
        # Clean the date before parsing
        game_date_str = clean_date(game['Date'])

        team1 = game['Tm']
        team2 = game['Opp']
        pitcher1 = "Unknown_Pitcher1"  # Placeholder for pitcher name (can be enhanced)
        pitcher2 = "Unknown_Pitcher2"  # Placeholder for pitcher name
        team1_odds = 100  # Replace with actual odds from dataset if available
        team2_odds = -110  # Replace with actual odds from dataset if available

        # Only run the Kelly Criterion bet check if the selected team is involved
        if team1 == team:
            result = run_main_py(team1, team2, pitcher1, pitcher2, team1_odds, team2_odds)
        else:
            continue  # Skip the game if the selected team is not team1
        
        if result is None:
            continue  # Skip if no result is returned or main.py fails

        # Simulate the win/loss from historical data for the selected team
        outcome = 1 if game['W/L'] == 'W' else 0  # 1 for win, 0 for loss

        # Parse the result from main.py to get the Kelly bet suggestion
        bet_size = extract_bet_size_from_result(result)  # This function should extract the bet size from the result
        edge = extract_edge_from_result(result)  # Extract edge percentage

        if bet_size > 0:  # Only calculate if a bet is suggested
            total_bets += 1
            if team1 == team:
                team_odds = team1_odds
            else:
                team_odds = team2_odds

            profit = calculate_profit_loss(bet_size, team_odds, outcome)

            # Track the biggest profit/loss
            if profit > 0:
                profitable_bets += 1
                biggest_profit = max(biggest_profit, profit)
            else:
                biggest_loss = min(biggest_loss, profit)

            bankroll += profit
            total_profit += profit
            profit_history.append((game['Date'], team1, team2, bet_size, profit))

        # Print the edge % in the progress message
        print(f"Processing game {idx + 1}/{max_games}... Edge for {team}: {edge:.2f}%")

    profitable_bet_percentage = (profitable_bets / total_bets) * 100 if total_bets > 0 else 0
    return total_bets, total_profit, biggest_profit, biggest_loss, bankroll, profitable_bet_percentage

def extract_bet_size_from_result(result):
    """
    Extract the Kelly Criterion suggested bet size from the output of main.py.
    """
    try:
        # Look for the line where the bet size is mentioned in result (e.g., "$100.00")
        match = re.search(r'\$([0-9]+(?:\.[0-9]+)?)', result)
        if match:
            return float(match.group(1))
        return 0
    except Exception:
        return 0

def backtest_team(team, year, initial_bankroll=1000):
    """
    Backtest a specific team's performance over a season using the main.py prediction logic.
    """
    print(f"Backtesting {team} for the {year} season...")

    # Ask the user how many games they want to backtest
    max_games = int(input(f"Enter the number of games to backtest for {team} in {year}: "))

    games = fetch_historical_data(team, year)
    if games is None:
        return

    total_bets, total_profit, biggest_profit, biggest_loss, final_bankroll, profitable_bet_percentage = simulate_betting_strategy(
        games, initial_bankroll, team, max_games)

    # Final output once the backtest is complete
    print("\nBacktest Results:")
    print(f"Total Bets: {total_bets}")
    print(f"Total Profit/Loss: {total_profit:.2f}")
    print(f"Biggest Profit: {biggest_profit:.2f}")
    print(f"Biggest Loss: {biggest_loss:.2f}")
    print(f"Ending Bankroll: {final_bankroll:.2f}")
    print(f"Profitable Bets: {profitable_bet_percentage:.2f}%")

if __name__ == "__main__":
    # Backtest the system for a specific team and year
    team = 'NYY'  # New York Yankees
    year = 2024
    backtest_team(team, year, initial_bankroll=103.58)
