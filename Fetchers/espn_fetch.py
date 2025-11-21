from espn_api.football import League
from datetime import datetime

def fetch_espn(league_id):
    try:
        year = datetime.now().year
        league = League(league_id=league_id, year=year)
        playoff_teams = league.settings.playoff_team_count
        playoff_weeks = league.finalScoringPeriod - league.settings.reg_season_count
        weeks_per_round = league.settings.playoff_matchup_period_length
        playoff_bye_weeks = abs(playoff_teams - (2 ** playoff_weeks // weeks_per_round))
        current_wins = {}
        teams = []
        for team in league.teams:
            teams.append(team.team_abbrev)
            current_wins[team.team_abbrev] = (team.wins, team.losses, team.ties, team.points_for)
        remaining_schedule = []
        current_week = league.current_week
        for week in range(current_week, league.settings.reg_season_count):
            box_scores = league.box_scores(week=week)
            for box_score in box_scores:
                remaining_schedule.append((
                    box_score.home_team.team_abbrev,
                    box_score.away_team.team_abbrev
                ))
        print(f"Playoff teams: {playoff_teams}, Bye teams: {playoff_bye_weeks}")
        return current_wins, remaining_schedule, teams, playoff_teams, playoff_bye_weeks
    except Exception as e:
        print(f"Error fetching data from ESPN API: {e}")
        return None, None, None, None, None