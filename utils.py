import requests
import streamlit as st
from datetime import datetime, timedelta

# ✅ Base URL for Balldontlie API (No API Key Required)
BALLEDONTLIE_BASE_URL = "https://www.balldontlie.io/api/v1"

# ✅ Fetch NBA games (Today/Tomorrow)

def get_api_sports_io_key():
    try:
        return st.secrets["API_SPORTS_IO_KEY"]
    except KeyError:
        st.error("Please add your api-sports.io API key to Streamlit secrets.")
        st.stop()

@st.cache_data(ttl=60)
def fetch_games(date):
    api_key = get_api_sports_io_key()
    url = f"https://api-sports.io/v1/fixtures?league=nba&date={date}&api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        games = []
        for game in data.get('response', []):
            home_team = game['teams']['home']['name']
            away_team = game['teams']['away']['name']
            games.append(f"{home_team} vs {away_team}")
        return games
    else:
        st.error(f"Failed to fetch games: HTTP {response.status_code}")
        return []

# ✅ Fetch player data by name (Balldontlie API)
def fetch_player_data(player_name):
    try:
        url = f"https://www.balldontlie.io/api/v1/players?search={player_name}"
        response = requests.get(url)

        if response.status_code == 404:
            return {"error": "Player not found. Try searching with a full name like 'LeBron James'."}
        elif response.status_code != 200:
            return {"error": f"API Error: {response.status_code}"}

        data = response.json()

        if not data.get("data"):
            return {"error": "No player data found. Check spelling or try a different name."}

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
