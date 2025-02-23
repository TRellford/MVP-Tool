import requests
import json
import streamlit as st
from nba_api.stats.endpoints import leaguegamefinder, playergamelogs, commonplayerinfo, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta

# ✅ NBA API Base Endpoint
NBA_API_URL = "https://stats.nba.com/stats/"

# ✅ Cache Data for Efficiency
@st.cache_data(ttl=3600)
def get_games_by_date(date):
    """Fetch NBA games for a specific date from NBA API."""
    date_str = date.strftime("%Y-%m-%d")
    gamefinder = leaguegamefinder.LeagueGameFinder(date_from_nullable=date_str, date_to_nullable=date_str)
    games = gamefinder.get_data_frames()[0]
    
    if games.empty:
        return []

    game_list = []
    for _, game in games.iterrows():
        game_list.append({
            "game_id": game["GAME_ID"],
            "home_team": game["MATCHUP"].split(" ")[-1],
            "away_team": game["MATCHUP"].split(" ")[0],
        })
    
    return game_list

# ✅ Fetch player data from NBA API
def fetch_player_data(player_name, selected_team=None):
    """Fetch player stats and head-to-head matchups from NBA API."""
    # 🔍 Search for player
    matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
    
    if not matching_players:
        st.error(f"🚨 Player '{player_name}' not found in NBA API.")
        return None, None

    player_id = matching_players[0]["id"]

    # 🔥 Get career stats
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]

    # 🔥 Get last 5, 10, 15 game logs
    game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2023-24").get_data_frames()[0]
    last_5 = game_logs.head(5).to_dict(orient="records")
    last_10 = game_logs.head(10).to_dict(orient="records")
    last_15 = game_logs.head(15).to_dict(orient="records")

    player_stats = {
        "Career Stats": career_stats.to_dict(orient="records"),
        "Last 5 Games": last_5,
        "Last 10 Games": last_10,
        "Last 15 Games": last_15
    }

    # 🔥 Head-to-Head Matchups This Season
    h2h_stats = []
    if selected_team:
        # Get team ID
        matching_teams = [t for t in teams.get_teams() if t["full_name"].lower() == selected_team.lower()]
        if matching_teams:
            team_id = matching_teams[0]["id"]
            
            # Filter game logs for matchups against selected team
            h2h_stats = [
                game for game in game_logs.to_dict(orient="records")
                if game["MATCHUP"].lower().startswith(selected_team.lower()) or game["MATCHUP"].lower().endswith(selected_team.lower())
            ]

    return player_stats, h2h_stats if h2h_stats else "No matchups this season."

@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch all active NBA players."""
    player_list = players.get_active_players()
    return [p["full_name"] for p in player_list]

@st.cache_data(ttl=3600)
def get_player_stats(player_name):
    """Fetch last 5, 10, 15 game logs for a player."""
    player_dict = {p["full_name"]: p["id"] for p in players.get_active_players()}
    player_id = player_dict.get(player_name)
    
    if not player_id:
        return None, None

    logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2023-24", last_n_games=15)
    df = logs.get_data_frames()[0]

    if df.empty:
        return None, None

    # Split into 5, 10, 15 game data
    last_5 = df.iloc[:5].to_dict(orient="records")
    last_10 = df.iloc[:10].to_dict(orient="records")
    last_15 = df.iloc[:15].to_dict(orient="records")

    return {"last_5": last_5, "last_10": last_10, "last_15": last_15}, get_h2h_stats(player_id)

@st.cache_data(ttl=3600)
def get_h2h_stats(player_id):
    """Fetch player performance against the upcoming opponent this season."""
    logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2023-24")
    df = logs.get_data_frames()[0]
    
    if df.empty:
        return "No head-to-head data available this season."
    
    return df.to_dict(orient="records")

@st.cache_data(ttl=3600)
def fetch_best_props(selected_game, min_odds=-250, max_odds=100):
    """Suggest best props within user-defined odds range."""
    # Mock data - Replace with real prop pulling logic
    props = [
        {"player": "LeBron James", "prop": "Points", "line": 27.5, "odds": -200, "insight": "LeBron has exceeded this line in 8 of his last 10 games."},
        {"player": "Anthony Davis", "prop": "Rebounds", "line": 11.5, "odds": -180, "insight": "Davis dominates the boards against weaker frontcourts."},
        {"player": "Jayson Tatum", "prop": "3PT Made", "line": 3.5, "odds": 110, "insight": "Tatum is hot from deep, hitting 4+ threes in 6 of his last 7 games."}
    ]

    return [prop for prop in props if min_odds <= prop["odds"] <= max_odds]

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, sgp_props, multi_game=False):
    """Build a Same Game Parlay based on user preferences."""
    # Mock AI-driven prop selection
    return f"SGP Generated for {selected_game} with selected props: {sgp_props}"

@st.cache_data(ttl=3600)
def fetch_game_predictions(selected_games):
    """Fetch AI-based game predictions."""
    # Mock predictions - Replace with AI model
    predictions = {
        game: {"ML": "Lakers", "Spread": "-4.5", "O/U": "215.5", "confidence_score": 78}
        for game in selected_games
    }
    return predictions

@st.cache_data(ttl=3600)
def fetch_sharp_money_trends(selected_games):
    """Fetch betting trends based on sharp money movement."""
    # Mock data
    return {game: "Sharp money favoring Lakers -4.5" for game in selected_games}

NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

def get_nba_odds(api_key):
    """Fetch NBA odds from The Odds API."""
    url = f"{NBA_ODDS_API_URL}?apiKey={api_key}&regions=us&markets=h2h,spreads,totals&oddsFormat=american"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching NBA odds: {response.status_code}")
        return []
import requests
import json

def fetch_nba_data(url, params=None):
    """Generic function to fetch NBA data with error handling."""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an error if the request fails

        if response.status_code == 200:
            try:
                return response.json()  # ✅ Ensure we return valid JSON
            except json.JSONDecodeError:
                print("🚨 Error: Invalid JSON response received!")
                return None
        else:
            print(f"🚨 API Error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
