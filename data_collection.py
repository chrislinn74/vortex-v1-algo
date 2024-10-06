import pybaseball as pb
import pandas as pd
import warnings
from unidecode import unidecode
from datetime import datetime
from utils import TEAM_ABBR_TO_NAME

warnings.simplefilter(action='ignore', category=FutureWarning)

def format_name_for_search(name):
    name_normalized = unidecode(name)
    full_name_format = name_normalized
    last_name_format = name_normalized.split()[-1]
    return [full_name_format, last_name_format]

def get_pitcher_stats(pitcher_name, year):
    try:
        search_names = format_name_for_search(pitcher_name)
        pitcher_stats = pb.pitching_stats(year, year, qual=0)
        pitcher_data = None
        for name in search_names:
            pitcher_data = pitcher_stats[pitcher_stats['Name'].str.contains(name, case=False, na=False)].copy()
            if not pitcher_data.empty:
                break

        if pitcher_data.empty:
            print(f"Stats not found for {pitcher_name} using name-based search.")
            return None

        era_minus = pitcher_data.iloc[0]['ERA-']
        fip_minus = pitcher_data.iloc[0]['FIP-']
        runs = pitcher_data.iloc[0]['R']
        earned_runs = pitcher_data.iloc[0]['ER']
        era = pitcher_data.iloc[0]['ERA']
        fip = pitcher_data.iloc[0]['FIP']
        whip = pitcher_data.iloc[0]['WHIP']
        lob_percentage = pitcher_data.iloc[0]['LOB%']

        return {
            'ERA-': era_minus,
            'FIP-': fip_minus,
            'R': runs,
            'ER': earned_runs,
            'ERA': era,
            'FIP': fip,
            'WHIP': whip,
            'LOB%': lob_percentage
        }
    except Exception as e:
        print(f"Error retrieving pitcher stats: {e}")
        return None

def get_team_stats(team, year, pitcher_name=None):
    batting_stats = pb.team_batting(year, year)
    pitching_stats = pb.team_pitching(year, year)

    if team not in batting_stats['Team'].values:
        raise ValueError(f"Team {team} not found in the batting stats for {year}.")
    
    if team not in pitching_stats['Team'].values:
        raise ValueError(f"Team {team} not found in the pitching stats for {year}.")
    
    team_batting = batting_stats[batting_stats['Team'] == team].iloc[0]
    team_pitching = pitching_stats[pitching_stats['Team'] == team].iloc[0]
    
    runs_scored = team_batting.get('R', 0)
    runs_allowed = team_pitching.get('R', 0)
    
    stats = {
        'run_differential': runs_scored - runs_allowed,
        'OPS': team_batting.get('OPS', 0),
        'SLG': team_batting.get('SLG', 0),
        'OBP': team_batting.get('OBP', 0),
        'XBH': team_batting.get('2B', 0) + team_batting.get('3B', 0) + team_batting.get('HR', 0),
        'Hits': team_batting.get('H', 0),
        'ISO': team_batting.get('ISO', 0),
        'RAR': team_batting.get('RAR', 0),
        'RBI': team_batting.get('RBI', 0),
        'LOB%': team_pitching.get('LOB%', 0),
        'RunsScored': runs_scored,
        'RunsAllowed': runs_allowed
    }

    used_pitcher_stats = False
    if pitcher_name:
        pitcher_stats = get_pitcher_stats(pitcher_name, year)
        if pitcher_stats is not None:
            stats.update({
                'ERA': pitcher_stats['ERA'],
                'FIP': pitcher_stats['FIP'],
                'WHIP': pitcher_stats['WHIP'],
                'ERA-': pitcher_stats['ERA-'],
                'FIP-': pitcher_stats['FIP-'],
                'R': pitcher_stats['R'],
                'ER': pitcher_stats['ER'],
                'LOB%': pitcher_stats['LOB%']
            })
            used_pitcher_stats = True
        else:
            print(f"No pitcher stats available for {pitcher_name}.")
    
    return stats, used_pitcher_stats

def get_team_rank(team, year):
    """Retrieve a team's rank within their division."""
    standings_list = pb.standings(year)
    standings = pd.concat(standings_list)
    team_name = TEAM_ABBR_TO_NAME.get(team, team)
    
    team_row = standings[standings['Tm'] == team_name]
    if not team_row.empty:
        rank = team_row.index[0] + 1  # Use index +1 for rank
        return rank
    else:
        print(f"Team '{team}' ({team_name}) not found in standings.")
        return None

def get_head_to_head(team1, team2, year):
    current_year = datetime.now().year
    if year > current_year:
        year = current_year

    try:
        schedule1 = pb.schedule_and_record(year, team1)
        if schedule1.empty and year == current_year:
            schedule1 = pb.schedule_and_record(year - 1, team1)
        
        if schedule1.empty:
            return None, None

        h2h_games = schedule1[schedule1['Opp'] == team2]
        team1_wins = h2h_games['W/L'].value_counts().get('W', 0)
        total_games = len(h2h_games)
        return team1_wins, total_games
    except Exception as e:
        print(f"Error getting head-to-head record: {e}")
        return None, None

def calculate_pythagorean_winning_percentage(runs_scored, runs_allowed):
    exponent = 1.83
    return (runs_scored ** exponent) / ((runs_scored ** exponent) + (runs_allowed ** exponent))