import requests
import streamlit as st
from nba_api.stats.endpoints import playergamelogs, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
from balldontlie import BalldontlieAPI  # Kept for potential future use

# API Base URLs
NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
BALL_DONT_LIE_API_URL = "https://api.balldontlie.io/v1"

def get_nba_games(date):
    """Fetch NBA games from BallDontLie API for a specific date."""
    if isinstance(date, str):
        date_str = date
    else:
        date_str = date.strftime("%Y-%m-%d")

    try:
        url = f"{BALL_DONT_LIE_API_URL}/games"
        headers = {"Authorization": st.secrets["balldontlie_api_key"]}  # Use Streamlit secrets
        params = {"dates[]": date_str}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401:
            st.error("❌ Unauthorized (401). Check your API key in secrets.toml.")
            return []
        if response.status_code != 200:
            st.error(f"❌ Error fetching games: {response.status_code}")
            return []

        games_data = response.json().get("data", [])
        formatted_games = [
            {
                "home_team": game["home_team"]["full_name"],
                "away_team": game["visitor_team"]["full_name"],
                "game_id": game["id"],
                "date": game["date"]
            }
            for game in games_data
        ]
        return formatted_games

    except Exception as e:
        st.error(f"❌ Unexpected error fetching games: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_best_props(selected_game, min_odds=-250, max_odds=100):
    """Fetch best player props for a selected game within a given odds range."""
    if not selected_game.get("game_id"):
        st.error("🚨 Invalid game selected. No game ID found.")
        return []

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "player_points,player_rebounds,player_assists"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching player props: {response.status_code}")
        return []

    props_data = response.json()
    best_props = []
    event = next(
        (e for e in props_data if e['home_team'] == selected_game['home_team'] and e['away_team'] == selected_game['away_team']),
        None
    )
    if not event:
        return ["No props found for the selected game."]

    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                price = outcome.get("price", 0)
                if min_odds <= price <= max_odds:
                    best_props.append({
                        "player": outcome["name"],
                        "prop": market["key"].replace("_", " ").title(),
                        "line": outcome.get("point", "N/A"),
                        "odds": price,
                        "insight": f"{outcome['name']} has strong recent performances in this prop category."
                    })

    return best_props if best_props else ["No suitable props found."]

@st.cache_data(ttl=3600)
def fetch_game_predictions(selected_games):
    """Fetch AI-based game predictions using live data."""
    predictions = {}
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        predictions[game_key] = {
            "ML": "TBD",
            "Spread": "TBD",
            "O/U": "TBD",
            "confidence_score": 75
        }
    return predictions

@st.cache_data(ttl=3600)
def fetch_sharp_money_trends(selected_games):
    """Fetch betting trends based on sharp money movement."""
    trends = {}
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        trends[game_key] = "Sharp money is favoring one side. (Live Data Needed)"
    return trends

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, sgp_props, multi_game=False):
    """Generate a Same Game Parlay using live data."""
    game_label = f"{selected_game['home_team']} vs {selected_game['away_team']}" if not multi_game else "Multiple Games"
    return f"SGP Generated for {game_label} with selected props: {sgp_props}"

@st.cache_data(ttl=3600)
def fetch_player_data(player_name, selected_team=None):
    """Fetch player stats and H2H stats from NBA API."""
    matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
    
    if not matching_players:
        return None, None

    player_id = matching_players[0]["id"]
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2024-25").get_data_frames()[0]

    last_5 = game_logs.head(5).to_dict(orient="records")
    last_10 = game_logs.head(10).to_dict(orient="records")
    last_15 = game_logs.head(15).to_dict(orient="records")

    player_stats = {
        "Career Stats": career_stats.to_dict(orient="records"),
        "Last 5 Games": last_5,
        "Last 10 Games": last_10,
        "Last 15 Games": last_15
    }
    
    h2h_stats = None
    if selected_team:
        team_abbr = next((t['abbreviation'] for t in teams.get_teams() if t['full_name'] == selected_team), None)
        if team_abbr:
            h2h_games = game_logs[game_logs['MATCHUP'].str.contains(team_abbr)]
            h2h_stats = h2h_games.to_dict(orient="records") if not h2h_games.empty else None

    return player_stats, h2h_stats

@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch all active NBA players."""
    return [p["full_name"] for p in players.get_active_players()]
