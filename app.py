from flask import Flask, render_template, request, jsonify
from playoff_pred import calculate_playoff_odds
from Fetchers.espn_fetch import fetch_espn
from Fetchers.sleeper_fetch import fetch_sleeper_playoff_odds_data
from Fetchers.csv_fetch import fetch_csv
import os
from werkzeug.utils import secure_filename

FETCHERS =  {
    'espn': fetch_espn,
    'sleeper': fetch_sleeper_playoff_odds_data
}

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/league/<source>/<int:league_id>')
def get_league_data(source, league_id):
    fetch_strategy = FETCHERS.get(source)
    if not fetch_strategy:
        return jsonify({'error': 'Unsupported source'}), 400
    current_wins, remaining_schedule, teams, playoff_teams, bye_teams = fetch_strategy(league_id)
    print(f"current_wins: {current_wins}")
    print(f"Remaining schedule: {remaining_schedule}")
    print(f"Teams: {teams}")

    playoff_odds, bye_odds, average_finishes = calculate_playoff_odds(num_simulations=100000, 
                                                                    schedule=remaining_schedule, 
                                                                    teams=teams, 
                                                                    current_wins=current_wins,
                                                                    playoff_teams=playoff_teams, 
                                                                    bye_teams=bye_teams)
    return jsonify({"playoff_odds": playoff_odds, "bye_odds": bye_odds, "average_finishes": average_finishes})

# @app.route('/api/sleeper_league/csv')
# def get_sleeper_csv_league_data():
#     current_wins, remaining_schedule, teams = fetch_csv()
#     print(f"current_wins: {current_wins}")
#     print(f"Remaining schedule: {remaining_schedule}")
#     print(f"Teams: {teams}")
#     playoff_odds, bye_odds, average_finishes = calculate_playoff_odds(num_simulations=100000, 
#                                                                       schedule=remaining_schedule, 
#                                                                       teams=teams, 
#                                                                       current_wins=current_wins, 
#                                                                       playoff_teams=playoff_teams, 
#                                                                       bye_teams=bye_teams)
#     return jsonify({"playoff_odds": playoff_odds, "bye_odds": bye_odds, "average_finishes": average_finishes})

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB max
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Ensure Fetchers/resources directory exists
    resources_dir = os.path.join(os.path.dirname(__file__), 'Fetchers', 'resources')
    os.makedirs(resources_dir, exist_ok=True)
    
    # Get uploaded files and playoff settings
    teams_file = request.files.get('teams_file')
    schedule_file = request.files.get('schedule_file')
    playoff_teams = int(request.form.get('playoff_teams', 6))
    bye_teams = int(request.form.get('bye_teams', 2))
    
    if not teams_file or not schedule_file:
        return jsonify({'error': 'Both files are required'}), 400
    
    # Helper function to check file extension
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    # Validate file extensions
    if not allowed_file(teams_file.filename) or not allowed_file(schedule_file.filename):
        return jsonify({'error': 'Only CSV files allowed'}), 400
    
    # Check file sizes
    teams_file.seek(0, os.SEEK_END)
    teams_size = teams_file.tell()
    teams_file.seek(0)
    
    schedule_file.seek(0, os.SEEK_END)
    schedule_size = schedule_file.tell()
    schedule_file.seek(0)
    
    if teams_size > MAX_FILE_SIZE or schedule_size > MAX_FILE_SIZE:
        return jsonify({'error': 'Files must be under 1MB'}), 400
    
    if teams_size == 0 or schedule_size == 0:
        return jsonify({'error': 'Files cannot be empty'}), 400
    
    # Validate CSV content by checking headers
    def validate_csv_content(file, expected_headers):
        try:
            first_line = file.readline().decode('utf-8', errors='ignore').strip()
            file.seek(0)
            
            # Check if expected headers are present
            for header in expected_headers:
                if header not in first_line:
                    return False, f"Missing required header: {header}"
            return True, None
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    # Validate teams file has required headers
    teams_valid, teams_error = validate_csv_content(teams_file, ['team_name', 'wins', 'losses', 'points_for'])
    if not teams_valid:
        return jsonify({'error': f'Invalid teams file: {teams_error}'}), 400
    
    # Validate schedule file has required headers
    schedule_valid, schedule_error = validate_csv_content(schedule_file, ['home_team', 'away_team'])
    if not schedule_valid:
        return jsonify({'error': f'Invalid schedule file: {schedule_error}'}), 400
    
    try:
        # Use secure_filename to sanitize filenames
        teams_filename = secure_filename(teams_file.filename)
        schedule_filename = secure_filename(schedule_file.filename)
        
        teams_path = os.path.join(resources_dir, teams_filename)
        schedule_path = os.path.join(resources_dir, schedule_filename)
        
        teams_file.save(teams_path)
        schedule_file.save(schedule_path)
        
        # Fetch and calculate
        current_wins, remaining_schedule, teams = fetch_csv(teams_path, schedule_path)
        
        # Validate playoff settings
        total_teams = len(teams)
        if playoff_teams > total_teams:
            return jsonify({'error': f'Playoff teams ({playoff_teams}) cannot exceed total teams ({total_teams})'}), 400
        
        if bye_teams >= playoff_teams:
            return jsonify({'error': f'Bye teams ({bye_teams}) must be less than playoff teams ({playoff_teams})'}), 400
        
        playoff_odds, bye_odds, average_finishes = calculate_playoff_odds(
            num_simulations=50000, 
            schedule=remaining_schedule, 
            teams=teams, 
            current_wins=current_wins,
            playoff_teams=playoff_teams,
            bye_teams=bye_teams
        )
        
        return jsonify({
            "playoff_odds": playoff_odds, 
            "bye_odds": bye_odds, 
            "average_finishes": average_finishes
        })
    except Exception as e:
        return jsonify({'error': 'Invalid CSV format or parsing error'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)