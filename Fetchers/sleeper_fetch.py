import requests

def fetch_request(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch league data: {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None
    
def get_team_data(rosters, users):
    current_wins = {}
    for roster in rosters:
        user_id = roster['owner_id']
        user = next((u for u in users if u['user_id'] == user_id), None)
        if user:
            team_name = user.get('display_name', 'Unknown')
            wins = roster.get('settings', {}).get('wins')
            loses = roster.get('settings', {}).get('losses')
            ties = roster.get('settings', {}).get('ties')
            points = roster.get('settings', {}).get('fpts')
            points_dec = roster.get('settings', {}).get('fpts_decimal', 0)
            points = points + (points_dec / 100.0) if points else None
            current_wins[team_name] = (wins, loses, ties, points)
        else:
            raise ValueError(f"User with ID {user_id} not found.")
    return current_wins

def get_roster_to_teamname_mapping(rosters, users):
    roster_to_teamname = {}
    for roster in rosters:
        user_id = roster['owner_id']
        user = next((u for u in users if u['user_id'] == user_id), None)
        if user:
            team_name = user.get('display_name', 'Unknown')
            roster_to_teamname[roster['roster_id']] = team_name
        else:
            raise ValueError(f"User with ID {user_id} not found.")
    return roster_to_teamname

def get_remaining_schedule(league_url, games_played, total_weeks, roster_to_teamname):
    remaining_schedule = []
    for week in range(games_played + 1, total_weeks):
        matchups = fetch_request(f"{league_url}/matchups/{week}")
        if matchups is None:
            return None
        matchup_dict = {}
        for matchup in matchups:
            team_name = roster_to_teamname.get(matchup["roster_id"], "Unknown")
            if matchup["matchup_id"] not in matchup_dict:
                matchup_dict[matchup["matchup_id"]] = [team_name]
            else:
                matchup_dict[matchup["matchup_id"]].append(team_name)

        for matchup_id in matchup_dict:
            teams = matchup_dict[matchup_id]
            if len(teams) == 2:
                remaining_schedule.append((teams[0], teams[1]))
            else:
                raise ValueError(f"Invalid matchup data for week {week}, matchup ID {matchup_id}: {teams}")
    return remaining_schedule

def fetch_sleeper_playoff_odds_data(league_id):
    league_url = f"https://api.sleeper.app/v1/league/{league_id}"
    try:
        users = fetch_request(f"{league_url}/users")
        if users is None:
            return None, None, None
        
        rosters = fetch_request(f"{league_url}/rosters")
        if rosters is None:
            return None, None, None
        
        league_settings = fetch_request(f"{league_url}")
        if league_settings is None:
            return None, None, None
        
        current_wins = get_team_data(rosters, users)
    
        record = rosters[0]['metadata'].get('record')
        if not record:
            raise ValueError("Record metadata not found in rosters.")
        games_played = len(record)
        roster_to_teamname = get_roster_to_teamname_mapping(rosters, users)
            
        remaining_schedule = []
        total_weeks = league_settings.get('settings', {}).get('playoff_week_start')
        remaining_schedule = get_remaining_schedule(league_url, games_played, total_weeks, roster_to_teamname)
  
        # Get list of team names
        team_names = list(current_wins.keys())
                
        print(f"Remaining schedule: {remaining_schedule}")
        
        return current_wins, remaining_schedule, team_names
        
    except Exception as e:
        print(f"Error fetching data from Sleeper API: {e}")
        return None, None, None
