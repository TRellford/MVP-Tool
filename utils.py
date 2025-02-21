import requests
import streamlit as st
from datetime import datetime, timedelta

# ✅ Base URL for Balldontlie API (No API Key Required)
BALLEDONTLIE_BASE_URL = "https://www.balldontlie.io/api/v1"

# ✅ Fetch NBA games (Today/Tomorrow)
def fetch_games(day_offset=0):
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        url = f"{BALLEDONTLIE_BASE_URL}/games?start_date={selected_date}&end_date={selected_date}"

        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return []

        data = response.json()

        if not data.get("data"):
            return ["No games available"]

        games_list = []
        for game in data["data"]:
            away_team = game["visitor_team"]["abbreviation"]
            home_team = game["home_team"]["abbreviation"]
            matchup = f"{away_team} v {home_team}"
            games_list.append(matchup)

        return games_list

    except Exception as e:
        st.error(f"Error fetching games: {str(e)}")
        return []

# ✅ Fetch player data by name
# ✅ Fetch player data by name (Balldontlie API)
def fetch_player_data(player_name):
    try:
        url = f"https://www.balldontlie.io/api/v1/players?search={player_name}"
        response = requests.get(url)

        if response.status_code != 200:
            return {"error": "Player not found"}

        data = response.json()
        if not data.get("data"):
            return {"error": "Player not found"}

        return data["data"]

    except Exception as e:
        return {"error": str(e)}

# ✅ Fetch player stats for the season
def fetch_player_stats(player_id):
    try:
        url = f"{BALLEDONTLIE_BASE_URL}/season_averages?player_ids[]={player_id}"
        response = requests.get(url)

        if response.status_code != 200:
            return {"error": "No stats found"}

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        return {"error": str(e)}
