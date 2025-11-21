from espn_api.football import League
from datetime import datetime

def fetch_espn(league_id):
    year = datetime.now().year
    league = League(league_id=league_id, year=year)
    current_wins = {}
    teams = []
    for team in league.teams:
        teams.append(team.team_abbrev)
        current_wins[team.team_abbrev] = (team.wins, team.losses, team.ties, team.points_for)
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