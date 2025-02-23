import streamlit as st
import datetime
import math
import requests
import streamlit.components.v1 as components
import unidecode
from utils import (
    fetch_player_data, fetch_best_props,
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends,
    fetch_all_players, fetch_best_props
)
from nba_api.stats.static import teams

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# Function to fetch NBA games from BallDontLie API
def get_games_by_date(date):
    """Fetch NBA games from BallDontLie API for a specific date."""
    try:
        date_str = date.strftime('%Y-%m-%d')
        url = f"https://api.balldontlie.io/v1/games?start_date={date_str}&end_date={date_str}"
        headers = {"Authorization": f"Bearer {st.secrets['ball_dont_lie_api_key']}"}  # Using Streamlit secrets
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            games = data.get("data", [])
            
            game_list = []
            for game in games:
                game_list.append({
                    "game_id": game["id"],
                    "home_team": game["home_team"]["full_name"],
                    "away_team": game["visitor_team"]["full_name"],
                    "date": game["date"]
                })
            return game_list
        else:
            st.error(f"Error fetching games: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching NBA games: {e}")
        return []

# --- Sidebar Navigation ---
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.selectbox("Select a Section:", ["Player Search", "Same Game Parlay", "SGP+", "Game Predictions"])

# --- Section 1: Player Search ---
if menu_option == "Player Search":
    st.header("🔍 Player Search & Prop Analysis")

    all_players = fetch_all_players()
    last_name_mapping = {p.split()[-1].lower(): p for p in all_players}

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

    player_name = st.text_input("Enter Player Name, Last Name, or Nickname", key="player_search")

    if player_name:
        selected_team = st.selectbox("Select Opponent for H2H Analysis (Optional)", ["None"] + [t["full_name"] for t in teams.get_teams()])
        selected_team = None if selected_team == "None" else selected_team

        player_stats, h2h_stats = fetch_player_data(player_name, selected_team)

        if player_stats:
            st.subheader(f"📈 {player_name} Stats - Last 5, 10, 15 Games")
            st.write(player_stats)

        if h2h_stats:
            st.subheader(f"🏀 {player_name} vs {selected_team} (This Season)")
            st.write(h2h_stats)

# --- Section 2: Same Game Parlay (SGP) ---
elif menu_option == "Same Game Parlay":
    st.header("🎯 Same Game Parlay (SGP) - One Game Only")

    date_option = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"], key="sgp_date")
    base_date = datetime.date.today()
    game_date = base_date if date_option == "Today's Games" else base_date + datetime.timedelta(days=1)
    
    available_games = get_games_by_date(game_date)
    
    st.write(f"📅 Fetching games for: {game_date.strftime('%Y-%m-%d')}")
    st.write(f"🎮 Number of games found: {len(available_games)}")

    if available_games:
        game_options = {f"{game['home_team']} vs {game['away_team']}": game for game in available_games}
        selected_game_label = st.selectbox("Select a Game:", list(game_options.keys()), key="sgp_game")
        selected_game = game_options[selected_game_label]
        st.write(f"🎯 Selected Game: {selected_game}")
    else:
        st.warning("🚨 No NBA games found for the selected date. This could be due to the All-Star break, off-season, or API issues.")
