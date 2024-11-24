from flask import Flask, render_template, jsonify, request
import os
from nba_api.stats.endpoints import leaguestandings, leaguegamefinder, teamdashboardbygeneralsplits, commonteamroster, playerdashboardbygeneralsplits
from nba_api.stats.static import teams
import pandas as pd
from datetime import datetime
import time
import json
import requests
from bs4 import BeautifulSoup
import re
from functools import lru_cache

app = Flask(__name__, 
    template_folder=os.path.abspath('templates'))

# Team metadata with colors and logos
TEAM_METADATA = {
    'Cleveland Cavaliers': {'wins': 16, 'losses': 1, 'conference': 'Eastern', 'conference_record': '12-1', 'division_record': '5-0', 'home_record': '9-0', 'away_record': '7-1', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '9-1', 'streak': 'W 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg'},
    'Boston Celtics': {'wins': 13, 'losses': 3, 'conference': 'Eastern', 'conference_record': '13-2', 'division_record': '4-0', 'home_record': '5-2', 'away_record': '8-1', 'neutral_record': '0-0', 'ot_record': '2-1', 'last_10': '8-2', 'streak': 'W 4', 'logo': 'https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg'},
    'Orlando Magic': {'wins': 11, 'losses': 7, 'conference': 'Eastern', 'conference_record': '8-3', 'division_record': '3-0', 'home_record': '8-0', 'away_record': '3-7', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '8-2', 'streak': 'W 2', 'logo': 'https://cdn.nba.com/logos/nba/1610612753/primary/L/logo.svg'},
    'New York Knicks': {'wins': 9, 'losses': 7, 'conference': 'Eastern', 'conference_record': '8-5', 'division_record': '3-1', 'home_record': '5-2', 'away_record': '4-5', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '6-4', 'streak': 'L 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg'},
    'Miami Heat': {'wins': 6, 'losses': 7, 'conference': 'Eastern', 'conference_record': '5-4', 'division_record': '2-1', 'home_record': '2-3', 'away_record': '3-4', 'neutral_record': '1-0', 'ot_record': '0-1', 'last_10': '4-6', 'streak': 'W 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612748/primary/L/logo.svg'},
    'Milwaukee Bucks': {'wins': 7, 'losses': 9, 'conference': 'Eastern', 'conference_record': '5-8', 'division_record': '3-3', 'home_record': '6-3', 'away_record': '1-6', 'neutral_record': '0-0', 'ot_record': '1-0', 'last_10': '6-4', 'streak': 'W 3', 'logo': 'https://cdn.nba.com/logos/nba/1610612749/primary/L/logo.svg'},
    'Chicago Bulls': {'wins': 7, 'losses': 10, 'conference': 'Eastern', 'conference_record': '6-4', 'division_record': '2-3', 'home_record': '2-5', 'away_record': '5-5', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '4-6', 'streak': 'W 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612741/primary/L/logo.svg'},
    'Atlanta Hawks': {'wins': 6, 'losses': 9, 'conference': 'Eastern', 'conference_record': '4-7', 'division_record': '2-4', 'home_record': '3-4', 'away_record': '3-5', 'neutral_record': '0-0', 'ot_record': '0-1', 'last_10': '3-7', 'streak': 'L 2', 'logo': 'https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg'},
    'Detroit Pistons': {'wins': 7, 'losses': 11, 'conference': 'Eastern', 'conference_record': '6-10', 'division_record': '0-4', 'home_record': '3-5', 'away_record': '4-6', 'neutral_record': '0-0', 'ot_record': '1-2', 'last_10': '4-6', 'streak': 'L 3', 'logo': 'https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg'},
    'Indiana Pacers': {'wins': 6, 'losses': 10, 'conference': 'Eastern', 'conference_record': '5-8', 'division_record': '1-1', 'home_record': '4-2', 'away_record': '2-8', 'neutral_record': '0-0', 'ot_record': '1-1', 'last_10': '4-6', 'streak': 'L 3', 'logo': 'https://cdn.nba.com/logos/nba/1610612754/primary/L/logo.svg'},
    'Brooklyn Nets': {'wins': 6, 'losses': 10, 'conference': 'Eastern', 'conference_record': '3-9', 'division_record': '0-5', 'home_record': '4-3', 'away_record': '2-7', 'neutral_record': '0-0', 'ot_record': '0-2', 'last_10': '3-7', 'streak': 'L 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612751/primary/L/logo.svg'},
    'Toronto Raptors': {'wins': 4, 'losses': 12, 'conference': 'Eastern', 'conference_record': '2-5', 'division_record': '1-1', 'home_record': '4-4', 'away_record': '0-8', 'neutral_record': '0-0', 'ot_record': '1-2', 'last_10': '3-7', 'streak': 'W 2', 'logo': 'https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg'},
    'Philadelphia 76ers': {'wins': 3, 'losses': 12, 'conference': 'Eastern', 'conference_record': '3-7', 'division_record': '1-2', 'home_record': '2-5', 'away_record': '1-7', 'neutral_record': '0-0', 'ot_record': '2-0', 'last_10': '2-8', 'streak': 'W 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg'},
    'Washington Wizards': {'wins': 2, 'losses': 12, 'conference': 'Eastern', 'conference_record': '2-8', 'division_record': '2-3', 'home_record': '1-5', 'away_record': '1-6', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '0-10', 'streak': 'L 10', 'logo': 'https://cdn.nba.com/logos/nba/1610612764/primary/L/logo.svg'},
    
    'Golden State Warriors': {'wins': 12, 'losses': 3, 'conference': 'Western', 'conference_record': '9-2', 'division_record': '0-2', 'home_record': '5-1', 'away_record': '7-2', 'neutral_record': '0-0', 'ot_record': '1-0', 'last_10': '8-2', 'streak': 'W 2', 'logo': 'https://cdn.nba.com/logos/nba/1610612744/primary/L/logo.svg'},
    'Oklahoma City Thunder': {'wins': 12, 'losses': 4, 'conference': 'Western', 'conference_record': '9-4', 'division_record': '3-1', 'home_record': '8-2', 'away_record': '4-2', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '6-4', 'streak': 'W 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612760/primary/L/logo.svg'},
    'Houston Rockets': {'wins': 12, 'losses': 5, 'conference': 'Western', 'conference_record': '7-3', 'division_record': '4-1', 'home_record': '8-2', 'away_record': '4-3', 'neutral_record': '0-0', 'ot_record': '0-1', 'last_10': '8-2', 'streak': 'W 2', 'logo': 'https://cdn.nba.com/logos/nba/1610612745/primary/L/logo.svg'},
    'Los Angeles Lakers': {'wins': 10, 'losses': 5, 'conference': 'Western', 'conference_record': '7-2', 'division_record': '2-1', 'home_record': '7-1', 'away_record': '3-4', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '7-3', 'streak': 'L 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg'},
    'LA Clippers': {'wins': 10, 'losses': 7, 'conference': 'Western', 'conference_record': '7-7', 'division_record': '4-2', 'home_record': '7-4', 'away_record': '3-3', 'neutral_record': '0-0', 'ot_record': '0-1', 'last_10': '7-3', 'streak': 'W 4', 'logo': 'https://cdn.nba.com/logos/nba/1610612746/primary/L/logo.svg'},
    'Denver Nuggets': {'wins': 8, 'losses': 6, 'conference': 'Western', 'conference_record': '4-6', 'division_record': '2-2', 'home_record': '5-3', 'away_record': '3-3', 'neutral_record': '0-0', 'ot_record': '2-0', 'last_10': '6-4', 'streak': 'L 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612743/primary/L/logo.svg'},
    'Phoenix Suns': {'wins': 9, 'losses': 7, 'conference': 'Western', 'conference_record': '7-5', 'division_record': '3-3', 'home_record': '5-3', 'away_record': '4-4', 'neutral_record': '0-0', 'ot_record': '1-1', 'last_10': '4-6', 'streak': 'L 5', 'logo': 'https://cdn.nba.com/logos/nba/1610612756/primary/L/logo.svg'},
    'Sacramento Kings': {'wins': 8, 'losses': 7, 'conference': 'Western', 'conference_record': '6-6', 'division_record': '1-3', 'home_record': '4-3', 'away_record': '4-4', 'neutral_record': '0-0', 'ot_record': '0-1', 'last_10': '5-5', 'streak': 'L 2', 'logo': 'https://cdn.nba.com/logos/nba/1610612758/primary/L/logo.svg'},
    'Dallas Mavericks': {'wins': 7, 'losses': 8, 'conference': 'Western', 'conference_record': '5-7', 'division_record': '2-2', 'home_record': '4-4', 'away_record': '3-4', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '3-7', 'streak': 'L 3', 'logo': 'https://cdn.nba.com/logos/nba/1610612742/primary/L/logo.svg'},
    'Utah Jazz': {'wins': 6, 'losses': 11, 'conference': 'Western', 'conference_record': '4-9', 'division_record': '1-4', 'home_record': '4-5', 'away_record': '2-6', 'neutral_record': '0-0', 'ot_record': '0-1', 'last_10': '3-7', 'streak': 'L 4', 'logo': 'https://cdn.nba.com/logos/nba/1610612762/primary/L/logo.svg'},
    'Memphis Grizzlies': {'wins': 5, 'losses': 12, 'conference': 'Western', 'conference_record': '2-10', 'division_record': '0-3', 'home_record': '2-6', 'away_record': '3-6', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '4-6', 'streak': 'L 1', 'logo': 'https://cdn.nba.com/logos/nba/1610612763/primary/L/logo.svg'},
    'Portland Trail Blazers': {'wins': 4, 'losses': 12, 'conference': 'Western', 'conference_record': '2-10', 'division_record': '1-4', 'home_record': '2-5', 'away_record': '2-7', 'neutral_record': '0-0', 'ot_record': '0-1', 'last_10': '2-8', 'streak': 'L 6', 'logo': 'https://cdn.nba.com/logos/nba/1610612757/primary/L/logo.svg'},
    'San Antonio Spurs': {'wins': 3, 'losses': 14, 'conference': 'Western', 'conference_record': '1-12', 'division_record': '0-4', 'home_record': '2-7', 'away_record': '1-7', 'neutral_record': '0-0', 'ot_record': '0-0', 'last_10': '0-10', 'streak': 'L 12', 'logo': 'https://cdn.nba.com/logos/nba/1610612759/primary/L/logo.svg'},
    'Minnesota Timberwolves': {'wins': 30, 'losses': 11, 'conference': 'Western', 'conference_record': '20-7', 'division_record': '7-2', 'home_record': '15-2', 'away_record': '15-9', 'neutral_record': '0-0', 'ot_record': '2-1', 'last_10': '7-3', 'streak': 'W2', 'logo': 'https://cdn.nba.com/logos/nba/1610612750/primary/L/logo.svg'}
}

def get_team_id(team_name):
    """Get team ID from team name"""
    team_dict = {team['full_name']: team['id'] for team in teams.get_teams()}
    return team_dict.get(team_name)

def get_team_standings():
    """Get current standings organized by conference"""
    standings = {'Eastern': [], 'Western': []}
    
    # Get the best record in each conference to calculate games behind
    best_records = {'Eastern': 0, 'Western': 0}
    for team_name, data in TEAM_METADATA.items():
        conf = data['conference']
        win_pct = data['wins'] / (data['wins'] + data['losses']) if data['wins'] + data['losses'] > 0 else 0
        best_records[conf] = max(best_records[conf], win_pct)
    
    for conference in ['Eastern', 'Western']:
        teams = [team for team_name, team in TEAM_METADATA.items() if team['conference'] == conference]
        sorted_teams = sorted(teams, key=lambda x: (-x['wins'], x['losses']))
        
        # Calculate games behind
        if sorted_teams:
            best_record = sorted_teams[0]
            best_wins = best_record['wins']
            best_losses = best_record['losses']
            
            for team in sorted_teams:
                gb = ((best_wins - team['wins']) + (team['losses'] - best_losses)) / 2.0
                team['games_behind'] = '%.1f' % gb if gb > 0 else '--'
                # Ensure neutral_record exists
                if 'neutral_record' not in team:
                    team['neutral_record'] = '0-0'
                
        standings[conference] = sorted_teams
    
    return standings

def get_head_to_head(team1, team2):
    """Get historical head-to-head records"""
    try:
        team1_id = get_team_id(team1)
        team2_id = get_team_id(team2)
        
        # Get games between these teams from the current season
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team1_id,
            vs_team_id_nullable=team2_id,
            season_nullable='2023-24'
        ).get_data_frames()[0]
        
        # Process the games
        last_games = []
        team1_wins = 0
        team2_wins = 0
        
        for _, game in gamefinder.iterrows():
            winner = team1 if game['WL'] == 'W' else team2
            if winner == team1:
                team1_wins += 1
            else:
                team2_wins += 1
                
            last_games.append({
                'date': game['GAME_DATE'],
                'winner': winner,
                'score': f"{game['PTS']}-{game['PLUS_MINUS'] if game['WL'] == 'W' else game['PTS'] - game['PLUS_MINUS']}"
            })
        
        return {
            'last_games': last_games,
            'season_record': {
                team1: team1_wins,
                team2: team2_wins
            }
        }
    except Exception as e:
        print(f"Error fetching head-to-head: {e}")
        return {
            'last_games': [],
            'season_record': {team1: 0, team2: 0}
        }

def get_team_advanced_stats(team_id):
    """Get advanced team statistics"""
    try:
        # Get team stats using NBA API
        stats = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
            team_id=team_id,
            season='2023-24',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]
        
        return {
            'offensive_rating': float(stats['OFF_RATING']),
            'defensive_rating': float(stats['DEF_RATING']),
            'net_rating': float(stats['NET_RATING']),
            'points_per_game': float(stats['PTS']),
            'points_allowed': float(stats['OPP_PTS']),
            'home_record': stats['W_HOME'],
            'away_record': stats['W_AWAY'],
            'last_10_games': stats['L10'],
        }
    except Exception as e:
        print(f"Error fetching advanced stats: {e}")
        return None

def get_team_top_players(team_id):
    """Get top players statistics for a team"""
    try:
        # Get team roster
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        player_stats = []
        
        # Get stats for each player
        for _, player in roster.iterrows():
            try:
                player_id = player['PLAYER_ID']
                stats = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
                    player_id=player_id,
                    season='2023-24',
                    per_mode_detailed='PerGame'
                ).get_data_frames()[0]
                
                if not stats.empty:
                    player_stats.append({
                        'name': player['PLAYER'],
                        'position': player['POSITION'],
                        'points': float(stats['PTS']),
                        'rebounds': float(stats['REB']),
                        'assists': float(stats['AST']),
                        'efficiency': float(stats['PTS']) + float(stats['REB']) + float(stats['AST']) - 
                                    (float(stats['FGA']) - float(stats['FGM'])) - 
                                    (float(stats['FTA']) - float(stats['FTM'])) - float(stats['TOV'])
                    })
                time.sleep(0.6)  # Respect API rate limits
            except Exception as e:
                print(f"Error fetching stats for player {player['PLAYER']}: {e}")
                continue
        
        # Sort players by efficiency rating
        player_stats.sort(key=lambda x: x['efficiency'], reverse=True)
        return player_stats[:8]  # Return top 8 players
        
    except Exception as e:
        print(f"Error fetching team roster: {e}")
        return None

def calculate_player_impact(players):
    """Calculate team's player impact score based on top players"""
    if not players:
        return 0.5  # Default value if no player data
        
    total_points = sum(player['points'] for player in players)
    total_efficiency = sum(player['efficiency'] for player in players)
    
    # Normalize the values
    avg_nba_team_points = 110  # NBA average
    avg_efficiency = 15 * 8  # Rough estimate for 8 players
    
    points_factor = min(total_points / avg_nba_team_points, 1.5)
    efficiency_factor = min(total_efficiency / avg_efficiency, 1.5)
    
    return (points_factor + efficiency_factor) / 2

def predict_game(team1, team2):
    """Generate prediction for a game between two teams"""
    try:
        # Get win percentages
        team1_wp = TEAM_METADATA[team1]['wins'] / (TEAM_METADATA[team1]['wins'] + TEAM_METADATA[team1]['losses'])
        team2_wp = TEAM_METADATA[team2]['wins'] / (TEAM_METADATA[team2]['wins'] + TEAM_METADATA[team2]['losses'])

        # Calculate probabilities
        total_wp = team1_wp + team2_wp
        team1_prob = (team1_wp / total_wp) * 100
        team2_prob = (team2_wp / total_wp) * 100

        # Calculate predicted scores (base score of 100 points adjusted by win percentage)
        base_score = 100
        team1_score = round(base_score * (1 + (team1_wp - 0.5)))
        team2_score = round(base_score * (1 + (team2_wp - 0.5)))

        return {
            'probabilities': {
                team1: round(team1_prob, 1),
                team2: round(team2_prob, 1)
            },
            'predicted_score': {
                team1: team1_score,
                team2: team2_score
            },
            'team_colors': {
                team1: TEAM_METADATA[team1]['primary_color'],
                team2: TEAM_METADATA[team2]['primary_color']
            },
            'team_logos': {
                team1: TEAM_METADATA[team1]['logo'],
                team2: TEAM_METADATA[team2]['logo']
            }
        }
        
    except Exception as e:
        print(f"Error in predict_game: {e}")
        return None

def get_nba_standings():
    """Fetch current NBA standings from stats.nba.com with proper headers"""
    url = "https://stats.nba.com/stats/leaguestandingsv3"
    params = {
        "LeagueID": "00",
        "Season": "2023-24",
        "SeasonType": "Regular Season"
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Referer": "https://www.nba.com/",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract standings data
        standings = data['resultSets'][0]['rowSet']
        headers = data['resultSets'][0]['headers']
        
        # Create a mapping of column names to indices
        header_map = {header: idx for idx, header in enumerate(headers)}
        
        return standings, header_map
    except requests.RequestException as e:
        print(f"Error fetching NBA standings: {e}")
        return None, None

@lru_cache(maxsize=1)
def cached_standings(cache_key=None):
    """Cache the standings for 1 hour"""
    return get_nba_standings()

def fetch_current_standings():
    """Update team metadata with current standings"""
    try:
        # Generate cache key based on current hour
        cache_key = datetime.now().strftime("%Y%m%d%H")
        
        # Get standings with caching
        standings, header_map = cached_standings(cache_key)
        
        if not standings or not header_map:
            print("Failed to fetch standings, using default data")
            return False
            
        # Update TEAM_METADATA with fresh standings
        for team in standings:
            team_city = team[header_map['TeamCity']]
            team_name = team[header_map['TeamName']]
            full_name = f"{team_city} {team_name}"
            
            if full_name in TEAM_METADATA:
                TEAM_METADATA[full_name].update({
                    'wins': team[header_map['WINS']],
                    'losses': team[header_map['LOSSES']],
                    'conference': 'Eastern' if team[header_map['Conference']] == 'East' else 'Western',
                    'last_10': team[header_map['L10']].strip(),
                    'streak': team[header_map['strCurrentStreak']].strip(),
                    'home_record': team[header_map['HOME']].strip(),
                    'away_record': team[header_map['ROAD']].strip()
                })
                print(f"Updated {full_name}: {team[header_map['WINS']]}-{team[header_map['LOSSES']]} ({team[header_map['strCurrentStreak']]})")
        
        print("Successfully updated standings from NBA.com")
        return True
        
    except Exception as e:
        print(f"Error updating standings: {str(e)}")
        print("Using default standings data")
        return False

@app.route('/')
def index():
    """Render the home page"""
    standings = get_team_standings()
    
    # Prepare teams data for the dropdowns
    teams = []
    for team_name, data in TEAM_METADATA.items():
        teams.append({
            'name': team_name,
            'conference': data['conference']
        })
    
    # Sort teams by conference and name
    teams.sort(key=lambda x: (x['conference'], x['name']))
    
    return render_template('index.html', standings=standings, teams=teams)

@app.route('/predict', methods=['POST'])
def predict_game():
    try:
        data = request.get_json()
        team1 = data['team1']
        team2 = data['team2']
        
        # Simple prediction logic (you can enhance this)
        team1_wins = TEAM_METADATA[team1]['wins']
        team1_losses = TEAM_METADATA[team1]['losses']
        team2_wins = TEAM_METADATA[team2]['wins']
        team2_losses = TEAM_METADATA[team2]['losses']
        
        team1_win_pct = team1_wins / (team1_wins + team1_losses) if (team1_wins + team1_losses) > 0 else 0
        team2_win_pct = team2_wins / (team2_wins + team2_losses) if (team2_wins + team2_losses) > 0 else 0
        
        # Calculate probability based on win percentages
        total = team1_win_pct + team2_win_pct
        if total == 0:
            probability = 0.5
        else:
            probability = team1_win_pct / total
            
        # Determine winner
        winner = team1 if probability > 0.5 else team2
        final_probability = probability if winner == team1 else (1 - probability)
        
        return jsonify({
            'winner': winner,
            'probability': final_probability
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Server starting... Access the website at http://127.0.0.1:5003")
    app.run(debug=True, host='127.0.0.1', port=5003)
