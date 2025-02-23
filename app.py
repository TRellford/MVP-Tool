import streamlit as st
import datetime
import math
import streamlit.components.v1 as components
import unidecode
from utils import (
    get_games_by_date, fetch_player_data, fetch_best_props,
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends,
    fetch_all_players, fetch_best_props
)
from nba_api.stats.static import teams

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

    # 🔍 Player Search
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

    selected_date = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"], key="sgp_date")
    # Use datetime.date for consistency
    base_date = datetime.date.today()
    game_date = base_date if selected_date == "Today's Games" else base_date + datetime.timedelta(days=1)
    # Pass as string in 'YYYY-MM-DD' format
    available_games = get_games_by_date(game_date.strftime('%Y-%m-%d'))

    # Debugging output in Streamlit
    st.write(f"📅 Fetching games for: {game_date.strftime('%Y-%m-%d')}")
    st.write(f"🎮 Number of games found: {len(available_games)}")

    if available_games:
        game_options = {f"{game['home_team']} vs {game['away_team']}": game for game in available_games}
        selected_game_label = st.selectbox("Select a Game:", list(game_options.keys()), key="sgp_game")
        selected_game = game_options[selected_game_label]
        st.write(f"🎯 Selected Game: {selected_game}")
    else:
        st.warning("🚨 No NBA games found for the selected date. This could be due to the All-Star break, off-season, or API data availability.")
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
