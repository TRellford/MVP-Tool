import requests
import streamlit as st
from datetime import datetime, timedelta

# ✅ Your API Key for The Odds API
THE_ODDS_API_KEY = "your_api_key_here"

# ✅ Fetch NBA games from The Odds API with correct date filtering
def fetch_games(day_offset=0):
    try:
        # Get the correct date
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

        # API URL (Ensure it's filtering by date)
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events?apiKey={THE_ODDS_API_KEY}"

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
            game_date = game.get("commence_time", "").split("T")[0]  # Extract the date
            if game_date == selected_date:  # ✅ Only include games matching the selected date
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

# ✅ Fetch player props from The Odds API
def fetch_player_props(game):
    try:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds?apiKey={THE_ODDS_API_KEY}&regions=us&markets=player_points,player_rebounds,player_assists"
        response = requests.get(url)

        if response.status_code == 401:
            return {"error": "API Error 401: Unauthorized. Check your API key."}
        elif response.status_code != 200:
            return {}

        return response.json()

    except Exception as e:
        return {"error": str(e)}
