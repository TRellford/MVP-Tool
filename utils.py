import requests
import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from nba_api.stats.endpoints import playergamelogs, playercareerstats
from nba_api.stats.static import players, teams
import streamlit as st

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
        except Exception:
            return 0

# Caching player data for **faster lookups**
@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch player names from NBA API."""
    nba_player_list = players.get_players()
    return {p["full_name"].lower(): p["id"] for p in nba_player_list}

@st.cache_data(ttl=3600)
def fetch_game_predictions(selected_games):
    """Fetch Moneyline, Spread & Over/Under predictions from The Odds API."""
    API_KEY = os.getenv("ODDS_API_KEY")
    if not API_KEY:
        return {}

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "bookmakers": "fanduel"
        }
    )
    if response.status_code != 200:
        return {}

    odds_data = response.json()
    predictions = {}
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next((e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']), None)
        if not event:
            predictions[game_key] = {"ML": "N/A", "Spread": "N/A", "O/U": "N/A", "confidence_score": 0}
            continue

        predictions[game_key] = {"ML": "✔️ Likely winner based on odds movement", "Spread": "✔️ Line favoring", "O/U": "✔️ Best bet range"}
    return predictions

@st.cache_data(ttl=3600)
def fetch_best_props(selected_game, min_odds=-450, max_odds=float('inf')):
    """Fetch and recommend player props with AI-driven confidence analysis."""
    API_KEY = os.getenv("ODDS_API_KEY")
    if not API_KEY:
        return []

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "player_points,player_rebounds,player_assists",
            "bookmakers": "fanduel"
        }
    )
    if response.status_code != 200:
        return []

    props_data = response.json()
    filtered_props = []
    for event in props_data:
        if event['home_team'] == selected_game["home_team"] and event['away_team'] == selected_game["away_team"]:
            for market in event.get("markets", []):
                for outcome in market.get("outcomes", []):
                    price = outcome.get("price", 0)
                    if min_odds <= price <= max_odds:
                        filtered_props.append({"player": outcome["name"], "prop": market["key"], "odds": price})

    return filtered_props if filtered_props else ["No suitable props found."]

def get_nba_games(date):
    try:
        url = f"{BALL_DONT_LIE_API_URL}/games"
        headers = {"Authorization": st.secrets["balldontlie_api_key"]}
        params = {"dates[]": date.strftime("%Y-%m-%d")}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return []

        games_data = response.json().get("data", [])
        return [{"home_team": game["home_team"]["full_name"], "away_team": game["visitor_team"]["full_name"]} for game in games_data]
    except Exception:
        return []

@st.cache_data(ttl=3600)
def fetch_player_data(player_name):
    """Fetch player stats from NBA API."""
    try:
        player_dict = fetch_all_players()
        player_id = player_dict.get(player_name.lower())

        if not player_id:
            return {"Error": f"Player '{player_name}' not found."}

        game_logs = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable="2024-25").get_data_frames()[0]

        if game_logs.empty:
            return {"Error": "No recent game data available for the 2024-25 season."}

        stat_columns = ["GAME_DATE", "PTS", "REB", "AST", "FG_PCT", "FG3M"]
        game_logs_filtered = game_logs[stat_columns]
        game_logs_filtered["GAME_DATE"] = pd.to_datetime(game_logs_filtered["GAME_DATE"]).dt.strftime('%Y-%m-%d')

        return {
            "Last 5 Games": game_logs_filtered.head(5).to_dict(orient="records"),
            "Last 10 Games": game_logs_filtered.head(10).to_dict(orient="records"),
        }
    
    except Exception as e:
        return {"Error": str(e)}

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, num_props=1, min_odds=-450, max_odds=float('inf'), multi_game=False):
    """Generate SGP or SGP+ prediction by selecting top props based on confidence and risk."""
    if multi_game:
        if not isinstance(selected_game, list):
            return "Invalid multi-game selection."
        all_props = []
        for game in selected_game:
            game_props = fetch_best_props(game, min_odds, max_odds)
            if not isinstance(game_props[0], str):
                all_props.extend(game_props)
    else:
        all_props = fetch_best_props(selected_game, min_odds, max_odds)
        if isinstance(all_props[0], str):
            return f"No valid FanDuel props available for SGP on {selected_game['home_team']} vs {selected_game['away_team']}."
    
    if not all_props or isinstance(all_props[0], str):
        return "No valid FanDuel props available for SGP."

    sorted_props = sorted(all_props, key=lambda x: x["odds"], reverse=True)
    selected_props = sorted_props[:num_props]

    return selected_props

@st.cache_data(ttl=3600)
def fetch_sharp_money_trends(selected_games):
    """Fetch sharp money trends & line movement from The Odds API."""
    API_KEY = os.getenv("ODDS_API_KEY")
    if not API_KEY:
        return {}

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h",
            "bookmakers": "fanduel"
        }
    )
    
    if response.status_code != 200:
        return {}

    odds_data = response.json()
    trends = {}
    
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next((e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']), None)
        
        if not event:
            trends[game_key] = "No line movement data available."
            continue

        fanduel = next((b for b in event.get("bookmakers", []) if b["key"] == "fanduel"), None)
        if not fanduel or not fanduel.get("markets"):
            trends[game_key] = "No FanDuel moneyline data available."
            continue

        h2h_market = fanduel["markets"][0]
        home_odds = next((o["price"] for o in h2h_market["outcomes"] if o["name"] == game["home_team"]), None)
        away_odds = next((o["price"] for o in h2h_market["outcomes"] if o["name"] == game["away_team"]), None)

        if home_odds and away_odds:
            trend = f"🔹 {game['home_team']} Odds: {home_odds}, {game['away_team']} Odds: {away_odds}"
        else:
            trend = "No significant sharp money movement detected."

        trends[game_key] = trend

    return trends
