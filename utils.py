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
    date_str = date.strftime("%Y-%m-%d")

    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
        games_data = scoreboard.get_data_frames()[0]  # Get the main games dataframe

        if games_data.empty:
            return []

        formatted_games = [
            {
                "home_team": row["HOME_TEAM_NAME"],
                "away_team": row["VISITOR_TEAM_NAME"],
                "game_id": row["GAME_ID"],
                "game_time": row["GAME_STATUS_TEXT"]
            }
            for _, row in games_data.iterrows()
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
