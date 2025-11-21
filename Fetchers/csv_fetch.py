import csv

def fetch_csv(team_file='Fetchers/resources/team_stats.csv', schedule_file='Fetchers/resources/remaining_schedule.csv'):
    current_wins = {}
    teams = []
    remaining_schedule = []

    try:
        with open(team_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"Row: {row}")
                team_name = row['team_name']
                wins = int(row['wins'])
                losses = int(row['losses'])
                ties = int(row.get('ties', 0))
                points = float(row['points_for'])
                teams.append(team_name)
                current_wins[team_name] = (wins, losses, ties, points)
        with open(schedule_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                home_team = row['home_team']
                away_team = row['away_team']
                remaining_schedule.append((home_team, away_team))

        return current_wins, remaining_schedule, teams
    except Exception as e:
        print(f"Error reading team file: {e}")
        return None, None, None