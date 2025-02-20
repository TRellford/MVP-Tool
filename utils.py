import requests
import streamlit as st
from datetime import datetime, timedelta

# ✅ Your API Key for The Odds API
THE_ODDS_API_KEY = "4c9fcd3030eac22e83179bf85a0cee0b"

# ✅ Fetch NBA games from The Odds API
def fetch_games(day_offset=0):
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events?apiKey={THE_ODDS_API_KEY}&date={selected_date}"

        response = requests.get(url)

        if response.status_code == 401:
            st.error("API Error 401: Unauthorized. Check your The Odds API key.")
            return []
        elif response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return []

        data = response.json()

        if not data:
            return ["No games available"]

        games_list = []
        for game in data:
            away_team = game.get("away_team", "Unknown")
            home_team = game.get("home_team", "Unknown")
            matchup = f"{away_team} v {home_team}"
            games_list.append(matchup)

        return games_list

    except Exception as e:
        st.error(f"Error fetching games: {str(e)}")
        return []

# ✅ Fetch sportsbook odds from The Odds API
def fetch_sportsbook_odds(game):
    try:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds?apiKey={THE_ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals"
        response = requests.get(url)

        if response.status_code == 401:
            return {"error": "API Error 401: Unauthorized. Check your API key."}
        elif response.status_code != 200:
            return {}

        return response.json()

    except Exception as e:
        return {"error": str(e)}
