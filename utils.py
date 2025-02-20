import requests
import streamlit as st
from datetime import datetime, timedelta

# ✅ Fetch NBA games for today or tomorrow
def fetch_games(day_offset=0):
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        url = f"https://api.nba.com/schedule?date={selected_date}"  # Replace with the correct API endpoint

        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"API Error: {response.status}")
            return []

        data = response.json()

        if "games" not in data or not data["games"]:
            return []

        games_list = []
        for game in data["games"]:
            away_team = game["awayTeam"]["teamTricode"]  # Example: CHA
            home_team = game["homeTeam"]["teamTricode"]  # Example: LAL
            matchup = f"{away_team} v {home_team}"
            games_list.append(matchup)

        return games_list

    except Exception as e:
        st.error(f"Error fetching games: {str(e)}")
        return []

# ✅ Fetch sportsbook odds (ML, Spread, O/U)
def fetch_sportsbook_odds(game):
    try:
        url = f"https://api.sportsbook.com/odds?game={game}"  # Replace with actual sportsbook API
        response = requests.get(url)
        if response.status_code != 200:
            return {}

        data = response.json()
        return data

    except Exception as e:
        return {"error": str(e)}

# ✅ Fetch player props (Live odds only)
def fetch_player_props(game):
    try:
        url = f"https://api.sportsbook.com/player-props?game={game}"  # Replace with actual sportsbook API
        response = requests.get(url)
        if response.status_code != 200:
            return {}

        return response.json()

    except Exception as e:
        return {"error": str(e)}

# ✅ Fetch real-time injury updates
def fetch_injury_updates():
    try:
        url = "https://api.nba.com/injuries"  # Replace with correct API
        response = requests.get(url)
        if response.status_code != 200:
            return {}

        return response.json()

    except Exception as e:
        return {"error": str(e)}
