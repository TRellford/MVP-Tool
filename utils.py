import requests
import streamlit as st
from nba_api.stats.endpoints import leaguegamefinder, playergamelogs, commonplayerinfo
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
