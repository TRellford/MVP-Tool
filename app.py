import streamlit as st
import datetime
import math
import streamlit.components.v1 as components
import unidecode
from utils import (
    get_games_by_date, fetch_player_data, fetch_best_props,
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends,
    fetch_all_players, get_player_stats
)

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.selectbox("Select a Section:", ["Player Search", "Same Game Parlay", "SGP+", "Game Predictions"])

# --- Section 1: Player Search ---
if menu_option == "Player Search":
    st.header("🔍 Player Search & Prop Analysis")

    # Fetch all players dynamically
    all_players = fetch_all_players()

    # Create a dictionary mapping last names to full names
    last_name_mapping = {p.split()[-1].lower(): p for p in all_players}

    # Nickname Mapping Dictionary
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

    # Select a game
    games = get_games_by_date(datetime.datetime.today())
    if games:
        st.subheader("📆 Today's Games")
        selected_game = st.selectbox("Select a Game", [f"{game['home_team']} vs {game['away_team']}" for game in games])

    # 🔍 Player Search
    player_name = st.text_input("Enter Player Name, Last Name, or Nickname", key="player_search")
    if player_name:
        player_stats, h2h_stats = get_player_stats(player_name)
        if player_stats:
            st.subheader(f"📈 {player_name} Stats - Last 5, 10, 15 Games")
            st.write(player_stats)
            st.subheader(f"🏀 {player_name} vs Selected Team (This Season)")
            st.write(h2h_stats if h2h_stats else "No head-to-head matchups this season.")

# --- Section 2: Same Game Parlay (SGP) ---
elif menu_option == "Same Game Parlay":
    st.header("🎯 Same Game Parlay (SGP) - One Game Only")

    selected_date = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"], key="sgp_date")
    game_date = datetime.datetime.today() if selected_date == "Today's Games" else datetime.datetime.today() + datetime.timedelta(days=1)
    available_games = get_games_by_date(game_date)

    selected_game = st.selectbox("Select a Game:", available_games, key="sgp_game")
    sgp_props = st.multiselect("Select Props for Same Game Parlay:", ["Points", "Assists", "Rebounds", "3PT Made"])

    if st.button("Generate SGP"):
        sgp_result = fetch_sgp_builder(selected_game, sgp_props)
        st.write(sgp_result)

    # AI-Optimized SGP Suggestion
    if st.button("Suggest Best SGP"):
        best_sgp = fetch_best_props(selected_game)
        st.write("🔹 **Best Value SGP Picks** based on AI analysis:")
        st.write(best_sgp)

# --- Section 3: Multi-Game Parlay (SGP+) ---
elif menu_option == "SGP+":
    st.header("🔥 Multi-Game Parlay (SGP+) - Select 2 to 12 Games")

    selected_games = st.multiselect("Select Games (Min: 2, Max: 12):", get_games_by_date(datetime.datetime.today()) + get_games_by_date(datetime.datetime.today() + datetime.timedelta(days=1)))

    if len(selected_games) < 2:
        st.warning("⚠️ You must select at least 2 games.")
    elif len(selected_games) > 12:
        st.warning("⚠️ You cannot select more than 12 games.")
    else:
        max_props_per_game = math.floor(24 / len(selected_games))
        props_per_game = st.slider(f"Choose Props Per Game (Max {max_props_per_game}):", 2, max_props_per_game)

        total_props = len(selected_games) * props_per_game
        st.write(f"✅ **Total Props Selected: {total_props} (Max: 24)**")

        if total_props > 24:
            st.error(f"🚨 Too many props selected! Max allowed: 24. You selected {total_props}. Reduce props per game.")
        else:
            if st.button("Generate SGP+"):
                sgp_plus_result = fetch_sgp_builder(selected_games, props_per_game, multi_game=True)
                st.write(sgp_plus_result)

# --- Section 4: Game Predictions ---
elif menu_option == "Game Predictions":
    st.header("📈 Moneyline, Spread & Over/Under Predictions")

    selected_games = st.multiselect("Select Games for Predictions:", get_games_by_date(datetime.datetime.today()) + get_games_by_date(datetime.datetime.today() + datetime.timedelta(days=1)))

    if len(selected_games) == 0:
        st.warning("⚠️ Please select at least one game.")
    else:
        if st.button("Get Game Predictions"):
            predictions = fetch_game_predictions(selected_games)

            if not predictions:
                st.warning("⚠️ No predictions available for selected games.")
            else:
                for game, pred in predictions.items():
                    confidence_score = pred.get("confidence_score", 50)  # Default 50 if not available
                    st.subheader(f"📊 {game} (Confidence: {confidence_score}%)")
                    st.progress(confidence_score / 100)
                    st.write(pred)

    # --- Sharp Money & Line Movement Tracker ---
    st.header("💰 Sharp Money & Line Movement Tracker")
    if len(selected_games) > 0 and st.button("Check Betting Trends"):
        sharp_trends = fetch_sharp_money_trends(selected_games)
        st.write(sharp_trends)
