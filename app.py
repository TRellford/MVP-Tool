import streamlit as st
import datetime
import math
import pandas as pd
import matplotlib.pyplot as plt
from utils import (
    fetch_player_data, fetch_best_props,
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends,
    fetch_all_players, get_nba_games
)
from nba_api.stats.static import teams

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- 🔹 Sidebar Navigation ---
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.selectbox("Select a Section:", ["Player Search", "Same Game Parlay", "SGP+", "Game Predictions"])

# --- 🔹 Player Search (Now Inside the Correct Section) ---
if menu_option == "Player Search":
    st.write("🔍 **Player Search Section**")

    # Fetch all player names once and store in session state
    if "player_list" not in st.session_state:
        st.session_state["player_list"] = fetch_all_players()

    # Function to filter players based on input
    def filter_players(search_input):
        if not search_input:
            return []
        return [name for name in st.session_state["player_list"] if search_input.lower() in name.lower()]

    # User types name, and we dynamically update suggestions
    search_input = st.text_input("Search for a Player:", "")
    filtered_players = filter_players(search_input)

    # If matches are found, let the user select from them
    if filtered_players:
        player_name = st.selectbox("Select a Player:", filtered_players)
    else:
        player_name = None

    # Search button
    if st.button("Search") and player_name:
        with st.spinner("Fetching player data..."):
            player_data = fetch_player_data(player_name)
            st.session_state["player_data"] = player_data  # Store in session state

    # Retrieve data from session state (if available)
    if "player_data" in st.session_state:
        player_data = st.session_state["player_data"]

        if "Error" in player_data:
            st.error(player_data["Error"])
        else:
            # Radio button for selecting the number of games to display
            selected_games = st.radio("Select Number of Games to Display:", ["Last 5 Games", "Last 10 Games"], index=0)

            # Display selected game logs
            game_logs = player_data.get(selected_games, [])

            if not game_logs:
                st.warning(f"No game data available for {selected_games}.")
            else:
                # Convert to DataFrame and remove the first column
                df = pd.DataFrame(game_logs)[["GAME_DATE", "PTS", "REB", "AST", "FG_PCT", "FG3M"]]

                # Ensure numerical formatting
                df["FG_PCT"] = df["FG_PCT"].round(2)  # FG% to 2 decimal places

                # Set index starting at 1 instead of 0
                df.index = range(1, len(df) + 1)

                # Display stats table
                st.subheader(f"{selected_games} Stats")
                st.dataframe(df)

                # Plot the stats (excluding "Minutes")
                st.subheader(f"{selected_games} Performance Graph")
                fig, ax = plt.subplots(figsize=(10, 5))
                df.set_index("GAME_DATE")[["PTS", "REB", "AST", "FG_PCT", "FG3M"]].plot(kind='bar', ax=ax)
                ax.set_title(f"{player_name} - {selected_games}")
                ax.set_xlabel("Game Date")
                ax.set_ylabel("Stats")
                ax.legend(loc="upper right")
                plt.xticks(rotation=45)
                st.pyplot(fig)

# --- 🎯 Same Game Parlay Section ---
elif menu_option == "Same Game Parlay":
    st.header("🎯 Same Game Parlay (SGP) - One Game Only")

    date_option = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"], key="sgp_date")
    base_date = datetime.date.today()
    game_date = base_date if date_option == "Today's Games" else base_date + datetime.timedelta(days=1)
    
    available_games = get_nba_games(game_date)
    
    st.write(f"📅 Fetching games for: {game_date.strftime('%Y-%m-%d')}")
    st.write(f"🎮 Number of games found: {len(available_games)}")

    if available_games:
        game_labels = [f"{game['home_team']} vs {game['away_team']}" for game in available_games]
        selected_game_label = st.selectbox("Select a Game:", game_labels, key="sgp_game")
        selected_game = next(g for g in available_games if f"{g['home_team']} vs {g['away_team']}" == selected_game_label)
        
        num_props = st.slider("Number of Props (1-8):", 1, 8, 1, key="sgp_num_props")
        
        if st.button("Generate SGP Prediction"):
            sgp_result = fetch_sgp_builder(selected_game, num_props=num_props)
            st.write(sgp_result)

# --- 🔥 Multi-Game Parlay (SGP+) Section ---
elif menu_option == "SGP+":
    st.header("🔥 Multi-Game Parlay (SGP+) - Select 2 to 12 Games")

    today_games = get_nba_games(datetime.date.today())
    tomorrow_games = get_nba_games(datetime.date.today() + datetime.timedelta(days=1))
    all_games = today_games + tomorrow_games
    game_labels = [f"{game['home_team']} vs {game['away_team']}" for game in all_games]
    selected_labels = st.multiselect("Select Games (Min: 2, Max: 12):", game_labels)
    selected_games = [g for g in all_games if f"{g['home_team']} vs {g['away_team']}" in selected_labels]

    if len(selected_games) >= 2:
        if st.button("Generate SGP+ Prediction"):
            sgp_plus_result = fetch_sgp_builder(selected_games, multi_game=True)
            st.write(sgp_plus_result)
    else:
        st.warning("⚠️ You must select at least 2 games.")

# --- 📈 Game Predictions Section ---
elif menu_option == "Game Predictions":
    st.header("📈 Moneyline, Spread & Over/Under Predictions")

    today_games = get_nba_games(datetime.date.today())
    tomorrow_games = get_nba_games(datetime.date.today() + datetime.timedelta(days=1))
    all_games = today_games + tomorrow_games
    game_labels = [f"{game['home_team']} vs {game['away_team']}" for game in all_games]
    selected_labels = st.multiselect("Select Games for Predictions:", game_labels)
    selected_games = [g for g in all_games if f"{g['home_team']} vs {g['away_team']}" in selected_labels]

    if len(selected_games) > 0:
        if st.button("Get Game Predictions"):
            predictions = fetch_game_predictions(selected_games)
            for game_label, pred in predictions.items():
                st.subheader(f"📊 {game_label}")
                st.write(f"Moneyline: {pred['ML']}")
                st.write(f"Spread: {pred['Spread']}")
                st.write(f"O/U: {pred['O/U']}")
    else:
        st.warning("⚠️ Please select at least one game.")
    else:
        if st.button("Get Game Predictions"):
            predictions = fetch_game_predictions(selected_games)
            if not predictions:
                st.warning("⚠️ No predictions available for selected games.")
            else:
                for game_label, pred in predictions.items():
                    confidence_score = pred.get("confidence_score", 50)
                    st.subheader(f"📊 {game_label} (Confidence: {confidence_score}%)")
                    st.progress(confidence_score / 100)
                    st.write(f"Moneyline: {pred['ML']}")
                    st.write(f"Spread: {pred['Spread']}")
                    st.write(f"O/U: {pred['O/U']}")

    st.header("💰 Sharp Money & Line Movement Tracker")
    if len(selected_games) > 0 and st.button("Check Betting Trends"):
        sharp_trends = fetch_sharp_money_trends(selected_games)
        for game_label, trend in sharp_trends.items():
            st.subheader(f"📉 {game_label}")
            st.write(trend)
