import streamlit as st
import datetime
import math
import streamlit.components.v1 as components
from utils import (
    get_games_by_date, fetch_player_data, fetch_best_props,
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends
)

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.selectbox("Select a Section:", ["Player Search", "Same Game Parlay", "SGP+", "Game Predictions"])

# --- Section 1: Player Search ---
if menu_option == "Player Search":
    st.header("🔍 Player Search & Prop Analysis")

    # Fetch all NBA players dynamically (Instead of hardcoding)
    all_players = sorted(fetch_all_players())  # Ensure `fetch_all_players()` is implemented in utils.py

    # Dictionary for nicknames
    nickname_mapping = {
        "Steph Curry": "Stephen Curry",
        "Bron": "LeBron James",
        "KD": "Kevin Durant",
        "AD": "Anthony Davis",
        "CP3": "Chris Paul",
    }

    # Use selectbox instead of text input for auto-suggest
    player_name = st.selectbox("Search for a Player:", all_players)

    # Convert nickname to full name if necessary
    player_name = nickname_mapping.get(player_name, player_name)

    st.write(f"🔍 Searching stats for: {player_name}")

    selected_props = st.multiselect(
        "Choose Props to Display:",
        ["Points", "Rebounds", "Assists", "3PT Made", "Blocks", "Steals"],
        default=["Points", "Rebounds", "Assists"]
    )

    trend_length = st.radio("Select Trend Length", [5, 10, 15])

    if st.button("Get Player Stats"):
        stats_df = fetch_player_data(player_name, trend_length)

        if "error" in stats_df:
            st.error(stats_df["error"])
        else:
            st.write(f"📊 **Stats for {player_name}:**")

            for prop in selected_props:
                if prop in stats_df.columns:
                    avg_value = stats_df[prop].mean()
                    st.subheader(f"📊 {prop} - Last {trend_length} Games (Avg: {round(avg_value, 1)})")
                    st.bar_chart(stats_df[["Game Date", prop]].set_index("Game Date"))
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
