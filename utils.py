import requests
import os
import streamlit as st
from nba_api.stats.endpoints import playergamelogs, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import pandas as pd

# API Base URLs
NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
BALL_DONT_LIE_API_URL = "https://api.balldontlie.io/v1"

class SGPAnalyzer:
    def __init__(self):
        self.all_players = players.get_players()
        self.all_teams = teams.get_teams()

    def get_player_stats(self, player_id, stat_key, games=5):
        """Fetch recent player stats for a specific stat."""
        try:
            game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2024-25").get_data_frames()[0]
            if not game_logs.empty:
                return game_logs[stat_key].head(games).mean()
            return 0
        except Exception as e:
            st.warning(f"⚠️ Error fetching stats for player {player_id}: {e}")
            return 0

def get_nba_games(date):
    """Fetch NBA games from Balldontlie API."""
    if isinstance(date, str):
        date_str = date
    else:
        date_str = date.strftime("%Y-%m-%d")

    try:
        url = f"{BALL_DONT_LIE_API_URL}/games"
        headers = {"Authorization": f"Bearer {st.secrets['balldontlie_api_key']}"}
        params = {"dates[]": date_str}

        response = requests.get(url, headers=headers, params=params)
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
def fetch_best_props(selected_game, min_odds=-450, max_odds=float('inf')):
    """Fetch and recommend FanDuel player props with AI-driven analysis, prioritizing high-confidence alt lines."""
    API_KEY = os.getenv("ODDS_API_KEY") 

    if not API_KEY:
        st.error("🚨 API Key for The Odds API is missing. Set `ODDS_API_KEY` in environment variables.")
        return []

    if not selected_game.get("game_id"):
        st.error("🚨 Invalid game selected. No game ID found.")
        return []

    game_date = selected_game.get("date", datetime.today().strftime("%Y-%m-%d")).split("T")[0]
    home_team = selected_game["home_team"]
    away_team = selected_game["away_team"]

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h",
            "date": game_date,
            "bookmakers": "fanduel"
        }
    )

    if response.status_code != 200:
        st.error(f"❌ Error fetching events: {response.status_code} - {response.text}")
        return []

    events_data = response.json()
    event = next(
        (e for e in events_data if e['home_team'] == home_team and e['away_team'] == away_team),
        None
    )

    if not event:
        st.warning(f"🚨 No matching event found for {home_team} vs {away_team} on {game_date}.")
        return []

    event_id = event["id"]
    event_url = f"{NBA_ODDS_API_URL.rsplit('/', 1)[0]}/events/{event_id}/odds"

    analyzer = SGPAnalyzer()
    markets = ["player_points", "player_rebounds", "player_assists", "player_threes"]
    best_props = {}

    for market in markets:
        response = requests.get(
            event_url,
            params={
                "apiKey": API_KEY,
                "regions": "us",
                "markets": market,
                "bookmakers": "fanduel"
            }
        )

        if response.status_code != 200:
            st.warning(f"⚠️ Skipping {market}: {response.status_code} - {response.text}")
            continue

        props_data = response.json()
        fanduel = next((b for b in props_data.get("bookmakers", []) if b["key"] == "fanduel"), None)
        if not fanduel:
            continue

        for m in fanduel.get("markets", []):
            for outcome in m.get("outcomes", []):
                price = outcome.get("price", 0)
                player_name = outcome["name"]
                prop_line = float(outcome.get("point", 0)) if outcome.get("point") != "N/A" else 0

                player = next((p for p in analyzer.all_players if p["full_name"] == player_name), None)
                if not player:
                    continue

                prop_key = f"{player_name}_{market}"

                # Fetch player stats
                recent_avg = analyzer.get_player_stats(player["id"], market.replace("player_", "").upper(), 5)
                confidence = stats.norm.cdf(recent_avg - prop_line) * 100  # Confidence estimation

                if prop_key not in best_props:
                    best_props[prop_key] = {
                        "player": player_name,
                        "prop": market.replace("player_", "").title(),
                        "main_line": prop_line,
                        "main_odds": price,
                        "main_confidence": confidence,
                        "alt_lines": []
                    }
                else:
                    if confidence > best_props[prop_key]["main_confidence"]:
                        best_props[prop_key]["alt_lines"].append({
                            "line": best_props[prop_key]["main_line"],
                            "odds": best_props[prop_key]["main_odds"],
                            "confidence": best_props[prop_key]["main_confidence"]
                        })
                        best_props[prop_key]["main_line"] = prop_line
                        best_props[prop_key]["main_odds"] = price
                        best_props[prop_key]["main_confidence"] = confidence
                    else:
                        best_props[prop_key]["alt_lines"].append({
                            "line": prop_line,
                            "odds": price,
                            "confidence": confidence
                        })

    final_props = []
    for prop in best_props.values():
        final_props.append({
            "player": prop["player"],
            "prop": prop["prop"],
            "line": prop["main_line"],
            "odds": prop["main_odds"],
            "confidence": prop["main_confidence"],
            "alt_lines": sorted(prop["alt_lines"], key=lambda x: -x["confidence"])
        })

    return final_props if final_props else ["No valid FanDuel props found."]

@st.cache_data(ttl=3600)
def fetch_player_data(player_name):
    """Fetch player stats from NBA API with proper game log retrieval, supporting nicknames."""
    try:
        nickname_mapping = {
            "Steph Curry": "Stephen Curry",
            "Bron": "LeBron James",
            "KD": "Kevin Durant",
            "AD": "Anthony Davis",
            "CP3": "Chris Paul",
            "Joker": "Nikola Jokic",
            "The Beard": "James Harden",
            "Dame": "Damian Lillard",
            "Klay": "Klay Thompson",
            "Tatum": "Jayson Tatum",
            "Giannis": "Giannis Antetokounmpo"
        }

        player_name = nickname_mapping.get(player_name, player_name)

        matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
        if not matching_players:
            return {"Error": f"Player '{player_name}' not found."}

        player_id = matching_players[0]["id"]
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
        game_logs = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable="2024-25").get_data_frames()[0]

        if game_logs.empty:
            return {"Career Stats": career_stats.to_dict(orient="records"), "Last 5 Games": [], "Last 10 Games": []}

        return {
            "Career Stats": career_stats.to_dict(orient="records"),
            "Last 5 Games": game_logs.head(5).to_dict(orient="records"),
            "Last 10 Games": game_logs.head(10).to_dict(orient="records"),
        }
    except Exception as e:
        return {"Error": str(e)}
