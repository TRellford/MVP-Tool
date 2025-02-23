import requests
import json
import streamlit as st
from nba_api.stats.endpoints import scoreboardv2, playergamelogs, commonplayerinfo, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta

# ✅ Default to Current NBA Season (2024-25)
CURRENT_SEASON = "2024-25"

# ✅ Cache Data for Efficiency
@st.cache_data(ttl=3600)
def get_games_by_date(date):
    """Fetch NBA games for a specific date from the NBA API."""
    date_str = date.strftime("%m/%d/%Y")  # Adjust to correct format for NBA API

    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
        games_data = scoreboard.get_data_frames()[0]  # Extract first DataFrame

        # 🔍 Debugging: Print Raw API Response
        print(f"🔍 RAW GAME DATA ({date_str}):", games_data)

        if games_data.empty:
            print("🚨 No games found for this date.")
            return []

        formatted_games = [
            {
                "home_team": row["HOME_TEAM_NAME"],
                "away_team": row["VISITOR_TEAM_NAME"],
                "game_id": row["GAME_ID"],
                "game_time": row["GAME_STATUS_TEXT"]
            }
            for _, row in games_data.iterrows()
            if "HOME_TEAM_NAME" in row and "VISITOR_TEAM_NAME" in row  # Ensure expected keys exist
        ]
        
        return formatted_games

    except Exception as e:
        print(f"❌ Error fetching scheduled games: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch all active NBA players."""
    player_list = players.get_active_players()
    return [p["full_name"] for p in player_list]

@st.cache_data(ttl=3600)
def fetch_player_data(player_name, selected_team=None):
    """Fetch player stats and head-to-head matchups from NBA API."""
    matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
    
    if not matching_players:
        st.error(f"🚨 Player '{player_name}' not found in NBA API.")
        return None, None

    player_id = matching_players[0]["id"]

    # 🔥 Get career stats
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]

    # 🔥 Get last 5, 10, 15 game logs
    game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable=CURRENT_SEASON).get_data_frames()[0]
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
        matching_teams = [t for t in teams.get_teams() if t["full_name"].lower() == selected_team.lower()]
        if matching_teams:
            team_id = matching_teams[0]["id"]
            
            # Filter game logs for matchups against selected team
            h2h_stats = [
                game for game in game_logs.to_dict(orient="records")
                if game["MATCHUP"].lower().startswith(selected_team.lower()) or game["MATCHUP"].lower().endswith(selected_team.lower())
            ]

    return
@st.cache_data(ttl=3600)
def fetch_best_props(selected_game, min_odds=-250, max_odds=100):
    """Fetch best player props for a selected game within a given odds range."""
    game_id = selected_game.get("game_id")  # Ensure we have a valid game ID
    if not game_id:
        st.error("🚨 Invalid game selected. No game ID found.")
        return []

    # 🔥 Replace with real API request for player props
    props_api_url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{game_id}/odds"
    response = requests.get(props_api_url, params={"apiKey": st.secrets["odds_api_key"], "regions": "us", "markets": "player_props"})

    if response.status_code != 200:
        st.error(f"❌ Error fetching player props: {response.status_code}")
        return []

    props_data = response.json()

    # Extract and filter props based on user-defined odds range
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
