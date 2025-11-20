from espn_api.football import League
from datetime import datetime
import requests

def fetch_espn(league_id):
    year = datetime.now().year
    league = League(league_id=league_id, year=year)
    current_wins = {}
    teams = league.teams
    for team in teams:
        current_wins[team.team_abbrev] = (team.wins, team.losses, team.points_for)
    remaining_schedule = []
    current_week = league.current_week
    for week in range(current_week, 18):
        box_scores = league.box_scores(week=week)
        for box_score in box_scores:
            if box_score.home_score == 0 and box_score.away_score == 0:
                remaining_schedule.append((
                    box_score.home_team.team_abbrev,
                    box_score.away_team.team_abbrev
                ))
    return current_wins, remaining_schedule, teams

def fetch_sleeper(league_id):
    year = datetime.now().year
    url = f"https://api.sleeper.app/v1/league/{league_id}"
    try:
        users = requests.get(f"{url}/league/{league_id}/users").json()
        return users
    except Exception as e:
        print(f"Error fetching data from Sleeper API: {e}")
        return None
