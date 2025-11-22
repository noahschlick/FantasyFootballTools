from espn_api.football import League
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

def fetch_week_matchups(league, week):
    try:
        matchups = league.scoreboard(week=week)
        return [(m.home_team.team_name, m.away_team.team_name) for m in matchups]
    except Exception as e:
        print(f"Warning: Could not fetch matchups for week {week}: {e}")
        return []

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
            teams.append(team.team_name)
            current_wins[team.team_name] = (team.wins, team.losses, team.ties, team.points_for)
        remaining_schedule = []
        current_week = league.current_week
        reg_season_count = league.settings.reg_season_count
        # Use scoreboard to get matchups for each remaining week
        # for week in range(current_week, league.settings.reg_season_count + 1):
        #     try:
        #         # scoreboard() returns matchups for a given week
        #         matchups = league.scoreboard(week=week)
        #         for matchup in matchups:
        #             remaining_schedule.append((
        #                 matchup.home_team.team_name,
        #                 matchup.away_team.team_name
        #             ))
        #     except Exception as e:
        #         print(f"Warning: Could not fetch matchups for week {week}: {e}")
        #         continue
        with ThreadPoolExecutor(max_workers=5)as executer:
            futures = [executer.submit(fetch_week_matchups, league, week)
                       for week in range(current_week, reg_season_count + 1)]
            for future in futures:
                remaining_schedule.extend(future.result())

        print(f"This is the remaining schedule: {remaining_schedule}")
      
        return current_wins, remaining_schedule, teams, playoff_teams, playoff_bye_weeks
    except Exception as e:
        print(f"Error fetching data from ESPN API: {e}")
        return None, None, None, None, None