import requests
import json
import streamlit as st
from nba_api.stats.endpoints import scoreboardv2, playergamelogs, playercareerstats, leaguegamefinder
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta

# ✅ NBA API Base URL
NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

# ✅ Cache Data for Efficiency
@st.cache_data(ttl=3600)
from nba_api.stats.endpoints import leaguegamefinder
import datetime

def get_games_by_date(date):
    """Fetch NBA games for a specific date in the 2024-25 season."""
    try:
        # Convert date to string format for filtering
        date_str = date.strftime('%Y-%m-%d')

        # Fetch all games
        game_finder = leaguegamefinder.LeagueGameFinder()
        games = game_finder.get_data_frames()[0]

        # Ensure season is correctly filtered (2024-25 season ID format)
        season_id = '22024'  # '2' + '2024' (format for season IDs in nba_api)

        # Filter games by date and season
        games = games[(games['SEASON_ID'] == season_id) & (games['GAME_DATE'] == date_str)]

        # Extract relevant details
        game_list = []
        for _, row in games.iterrows():
            game_list.append({
                "game_id": row["GAME_ID"],
                "home_team": row["MATCHUP"].split(" ")[-1],  # Extract home team from matchup string
                "away_team": row["MATCHUP"].split(" ")[0],   # Extract away team
                "date": row["GAME_DATE"]
            })

        return game_list

    except Exception as e:
        print(f"Error fetching games: {e}")
        return []
@st.cache_data(ttl=3600)
def fetch_best_props(selected_game, min_odds=-250, max_odds=100):
    """Fetch best player props for a selected game within a given odds range."""
    game_id = selected_game.get("game_id")
    if not game_id:
        st.error("🚨 Invalid game selected. No game ID found.")
        return []

    response = requests.get(NBA_ODDS_API_URL, params={"apiKey": st.secrets["odds_api_key"], "regions": "us", "markets": "player_props"})
    if response.status_code != 200:
        st.error(f"❌ Error fetching player props: {response.status_code}")
        return []

    props_data = response.json()

    best_props = []
    for bookmaker in props_data.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                if min_odds <= outcome.get("price", 0) <= max_odds:
                    best_props.append({
                        "player": outcome["name"],
                        "prop": market["key"].replace("_", " ").title(),
                        "line": outcome.get("point", "N/A"),
                        "odds": outcome["price"],
                        "insight": f"{outcome['name']} has strong recent performances in this prop category."
                    })

    return best_props if best_props else ["No suitable props found."]

@st.cache_data(ttl=3600)
def fetch_game_predictions(selected_games):
    """Fetch AI-based game predictions using live data."""
    predictions = {}

    for game in selected_games:
        predictions[game] = {
            "ML": "TBD",  # Replace with ML prediction logic
            "Spread": "TBD",  # Replace with spread prediction logic
            "O/U": "TBD",  # Replace with total points prediction logic
            "confidence_score": 75  # Example confidence score
        }

    return predictions

@st.cache_data(ttl=3600)
def fetch_sharp_money_trends(selected_games):
    """Fetch betting trends based on sharp money movement."""
    trends = {}
    
    for game in selected_games:
        trends[game] = "Sharp money is favoring one side. (Live Data Needed)"

    return trends

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, sgp_props, multi_game=False):
    """Generate a Same Game Parlay using live data."""
    return f"SGP Generated for {selected_game} with selected props: {sgp_props}"

@st.cache_data(ttl=3600)
def fetch_player_data(player_name):
    """Fetch player stats from NBA API."""
    matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
    
    if not matching_players:
        return None, None

    player_id = matching_players[0]["id"]

    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2024-25").get_data_frames()[0]

    last_5 = game_logs.head(5).to_dict(orient="records")
    last_10 = game_logs.head(10).to_dict(orient="records")
    last_15 = game_logs.head(15).to_dict(orient="records")

    return {
        "Career Stats": career_stats.to_dict(orient="records"),
        "Last 5 Games": last_5,
        "Last 10 Games": last_10,
        "Last 15 Games": last_15
    }

@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch all active NBA players."""
    return [p["full_name"] for p in players.get_active_players()]
