# Monte Carlo simulator for fantasy playoffs
# - Edit teams, current_wins, schedule (list of remaining matches as pairs)
# - Assumes remaining games are 50/50; ties not modeled (but could be added)
# - Tiebreakers: coin flip among tied teams for playoff/bye placement

import random
from collections import defaultdict
import math


teams_to_player_names = {
    "TeamA": ["Noah"],
    "TeamB": ["Dylan"],
    "TeamC": ["Ethan"],
    "TeamD": ["Beaman"],
    "TeamE": ["Pat"],
    "TeamF": ["Vondy"],
    "TeamG": ["Hailey"],
    "TeamH": ["Nathan"],
    "TeamI": ["Jonathan"],
    "TeamJ": ["Marshall"],
    "TeamK": ["Javi"],
    "TeamL": ["Ashlyn"]
}

teams = [
    "TeamA","TeamB","TeamC","TeamD","TeamE","TeamF",
    "TeamG","TeamH","TeamI","TeamJ","TeamK","TeamL"
]

# current wins and points. Format: (wins, points)
current_wins = {
    "TeamA": (8, 3, 1479.74), "TeamB": (9, 2, 1368.38), "TeamC": (7, 4, 1385.00), "TeamD": (8, 3, 1443.62),
    "TeamE": (7, 4, 1297.58), "TeamF": (5, 6, 1208.72), "TeamG": (4, 7, 1302.54), "TeamH": (5, 6, 1271.86),
    "TeamI": (5, 6, 1180.96), "TeamJ": (4, 7, 1056.94), "TeamK": (3, 8, 1302.36), "TeamL": (1, 10, 990.18)
}

# remaining schedule: list of (home, away) matchups
# fill with actual remaining games; example placeholders
schedule = [
    # # week 11
    # ("TeamA","TeamK"), ("TeamC","TeamD"), ("TeamE","TeamL"),
    # ("TeamI","TeamF"), ("TeamB","TeamG"), ("TeamJ","TeamH"),
    # week 12
    ("TeamA","TeamD"), ("TeamC","TeamK"), ("TeamE","TeamH"),
    ("TeamI","TeamB"), ("TeamG","TeamF"), ("TeamJ","TeamL"),
    # week 13
    ("TeamA","TeamL"), ("TeamC","TeamF"), ("TeamE","TeamI"),
    ("TeamB","TeamH"), ("TeamG","TeamK"), ("TeamJ","TeamD"),
    # week 14
    ("TeamA","TeamJ"), ("TeamC","TeamG"), ("TeamE","TeamB"),
    ("TeamI","TeamH"), ("TeamF","TeamK"), ("TeamD","TeamL"),
]


def calculate_playoff_odds(num_simulations=50000, schedule=schedule, teams=teams, current_wins=current_wins):
    """
    Calculate the probability of each team making the playoffs.
    
    Parameters:
    - num_simulations: number of Monte Carlo simulations to run (default 10000)
    
    Returns:
    - playoff_odds: dict with team names as keys and playoff probability as values
    - bye_odds: dict with team names as keys and bye (top 2 seed) probability as values
    - average_finishes: dict with team names as keys and average finishing position as values
    
    The playoffs consist of 6 teams, ranked by:
    1. Most wins
    2. Highest points scored (tiebreaker)
    
    Top 2 teams receive byes to week 16.
    
    IMPORTANT: Points fluctuate randomly in remaining games with variance.
    Each week, each team scores between 70% and 130% of league average.
    """
    
    playoff_teams = 6
    bye_teams = 2
    
    # Calculate each team's average points per game
    # This allows teams to regress toward their own average, not league average
    team_avg_ppg = {}
    for team in teams:
        wins, loses, points = current_wins[team]
        # Estimate games played (assume ~11 weeks played so far)
        games_played = wins + loses
        avg_ppg = points / games_played
        team_avg_ppg[team] = avg_ppg
    
    # Calculate league-wide statistics for reference
    all_avg_ppg = list(team_avg_ppg.values())
    league_avg_ppg = sum(all_avg_ppg) / len(all_avg_ppg)
    
    # Standard deviation of team PPGs (how much variance exists week-to-week)
    # Using ~12% of average as typical fantasy football variance
    league_std_dev = league_avg_ppg * 0.50
    
    # Track outcomes across all simulations
    playoff_count = defaultdict(int)
    bye_count = defaultdict(int)
    finish_position_sum = defaultdict(int)
    
    for _ in range(num_simulations):
        # Initialize team records for this simulation
        sim_record = {}
        for team in teams:
            wins, loses, points = current_wins[team]
            sim_record[team] = [wins, points]
        
        # Simulate remaining games
        for home, away in schedule:
            # Generate random points using normal distribution around each team's average
            # This creates mean-reversion: teams tend to score near their average
            # but can have outlier weeks (good or bad)
            home_points = random.gauss(team_avg_ppg[home], league_std_dev)
            away_points = random.gauss(team_avg_ppg[away], league_std_dev)
            
            # Ensure points don't go negative
            home_points = max(0, home_points)
            away_points = max(0, away_points)
            
            # Determine winner based on who scored more
            if home_points > away_points:
                sim_record[home][0] += 1  # Home team wins
            else:
                sim_record[away][0] += 1  # Away team wins
            
            # Both teams add their scored points
            sim_record[home][1] += home_points
            sim_record[away][1] += away_points
        
        # Rank teams by wins (primary) and points (tiebreaker)
        ranked_teams = sorted(
            teams,
            key=lambda t: (sim_record[t][0], sim_record[t][1]),
            reverse=True
        )
        
        # Track playoff and bye teams
        for idx, team in enumerate(ranked_teams):
            finish_position_sum[team] += idx + 1
            
            if idx < playoff_teams:
                playoff_count[team] += 1
                
                if idx < bye_teams:
                    bye_count[team] += 1
    
    # Calculate probabilities
    for team in teams:
        print(f"Playoff count {team}: {playoff_count[team]}")
    playoff_odds = {
        team: playoff_count[team] / num_simulations
        for team in teams
    }
    
    bye_odds = {
        team: bye_count[team] / num_simulations
        for team in teams
    }
    
    average_finishes = {
        team: finish_position_sum[team] / num_simulations
        for team in teams
    }
    
    return playoff_odds, bye_odds, average_finishes


def print_playoff_odds_report(num_simulations=50000, playoff_odds=None, bye_odds=None, average_finishes=None):
    """
    Print a formatted report of playoff odds for all teams.
    """
    
    print(f"\n{'='*80}")
    print(f"PLAYOFF ODDS REPORT (Based on {num_simulations} simulations)")
    print(f"{'='*80}\n")
    
    print(f"{'Team':<10} {'Player':<15} {'Playoff %':<15} {'Bye %':<15} {'Avg Finish':<15}")
    print("-" * 80)
    
    # Sort by playoff odds (descending)
    sorted_teams = sorted(
        teams,
        key=lambda t: playoff_odds[t],
        reverse=True
    )
    
    for team in sorted_teams:
        player_name = teams_to_player_names[team][0]
        playoff_pct = playoff_odds[team] * 100
        bye_pct = bye_odds[team] * 100
        avg_finish = average_finishes[team]
        
        print(f"{team:<10} {player_name:<15} {playoff_pct:>8.4f}%        {bye_pct:>6.1f}%        {avg_finish:>6.2f}")
    
    print(f"\n{'='*80}\n")

def main():
    playoff_odds, bye_odds, average_finishes = calculate_playoff_odds(num_simulations=100000, schedule=schedule, teams=teams, current_wins=current_wins)
    print_playoff_odds_report(num_simulations=100000, playoff_odds=playoff_odds, bye_odds=bye_odds, average_finishes=average_finishes)

if __name__ == "__main__":
    main()