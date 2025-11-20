from flask import Flask, render_template, request, jsonify
from playoff_pred import calculate_playoff_odds, print_playoff_odds_report
from espn_api.football import League
from fetchers import fetch_espn, fetch_sleeper

FETCHERS =  {
    'espn': fetch_espn,
    'sleeper': fetch_sleeper
}

app = Flask(__name__)

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

@app.route('/')
def index():
    playoff_odds, bye_odds, average_finishes = calculate_playoff_odds(num_simulations=10000, schedule=schedule, teams=teams, current_wins=current_wins)
    
    # Format results for JSON response
    results = []
    for team in teams:
        results.append({
            'team': team,
            'player': teams_to_player_names[team][0],
            'playoff_odds': round(playoff_odds[team] * 100, 2),
            'bye_odds': round(bye_odds[team] * 100, 2),
            'avg_finish': round(average_finishes[team], 2)
        })
    
    # Sort by playoff odds
    results.sort(key=lambda x: x['playoff_odds'], reverse=True)
    
    return jsonify(results)

@app.route('/api/espn_league/<int:league_id>')
def get_espn_league_data(league_id):
    fetch_strategy = FETCHERS.get('espn')
    current_wins, remaining_schedule, teams = fetch_strategy(league_id)

    print(f"Remaining schedule: {remaining_schedule}")
    print(f"Teams: {teams}")
    return jsonify(current_wins)

@app.route('/api/league/<source>/<int:league_id>')
def get_league_data(source, league_id):
    fetch_strategy = FETCHERS.get(source)
    if not fetch_strategy:
        return jsonify({'error': 'Unsupported source'}), 400
    users = fetch_strategy(league_id)
    print(f"Users: {users}")
    return jsonify(users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)