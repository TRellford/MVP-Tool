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

st.sidebar.title("🔍 Navigation")
new_menu_option = st.sidebar.selectbox(
    "Select a Section:",
    ["Player Search", "Same Game Parlay", "SGP+", "Game Predictions"],
    key="nav_selectbox"
)

# Force rerun if menu_option changes
if new_menu_option != st.session_state.menu_option:
    st.session_state.menu_option = new_menu_option
    st.rerun()  # Explicitly rerun the app to reflect the new section

# Player Search
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
            
# Same Game Parlay
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
        
        # Define risk levels with odds ranges and Unicode emojis
        risk_levels = [
            {"risk": "Very Safe", "emoji": "🔵", "min_odds": -450, "max_odds": -300},
            {"risk": "Safe", "emoji": "🟢", "min_odds": -299, "max_odds": -200},
            {"risk": "Moderate Risk", "emoji": "🟡", "min_odds": -199, "max_odds": 100},
            {"risk": "High Risk", "emoji": "🟠", "min_odds": 101, "max_odds": 250},
            {"risk": "Very High Risk", "emoji": "🔴", "min_odds": 251, "max_odds": float('inf')}
        ]
        
        # Format options to match your exact specification
        risk_options = [
            f"{level['risk']} ({level['min_odds']} to {'+' + str(level['max_odds']) if level['max_odds'] > 0 and level['max_odds'] != float('inf') else str(level['max_odds']) if level['max_odds'] != float('inf') else '+∞'}) {level['emoji']}"
            for level in risk_levels
        ]
        st.write("Select a risk level to filter each prop’s odds:")
        risk_index = st.selectbox("Risk Level (Odds Range for Each Prop):", risk_options, key="sgp_risk_level")
        
        # Extract the selected risk data
        selected_risk = next(level for level in risk_levels if f"{level['risk']} ({level['min_odds']} to {'+' + str(level['max_odds']) if level['max_odds'] > 0 and level['max_odds'] != float('inf') else str(level['max_odds']) if level['max_odds'] != float('inf') else '+∞'}) {level['emoji']}" == risk_index)
        risk_level = selected_risk["risk"]
        min_odds = selected_risk["min_odds"]
        max_odds = selected_risk["max_odds"]
        
        if st.button("Generate SGP Prediction"):
            sgp_result = fetch_sgp_builder(selected_game, num_props=num_props, min_odds=min_odds, max_odds=max_odds)
            st.write(sgp_result)
    else:
        st.warning("🚨 No NBA games found for the selected date.")
# SGP+
elif menu_option == "SGP+":
    st.header("🔥 Multi-Game Parlay (SGP+) - Select 2 to 12 Games")

    today_games = get_nba_games(datetime.date.today())
    tomorrow_games = get_nba_games(datetime.date.today() + datetime.timedelta(days=1))
    all_games = today_games + tomorrow_games
    game_labels = [f"{game['home_team']} vs {game['away_team']}" for game in all_games]
    selected_labels = st.multiselect("Select Games (Min: 2, Max: 12):", game_labels)
    selected_games = [g for g in all_games if f"{g['home_team']} vs {g['away_team']}" in selected_labels]

    if len(selected_games) < 2:
        st.warning("⚠️ You must select at least 2 games.")
    elif len(selected_games) > 12:
        st.warning("⚠️ You cannot select more than 12 games.")
    else:
        max_props_per_game = math.floor(24 / len(selected_games))
        props_per_game = st.slider(f"Choose Props Per Game (Max {max_props_per_game}):", 1, max_props_per_game)
        
        # Risk level selection with colors
        risk_levels = [
            ("Very Safe", "blue", (-450, -300)),
            ("Safe", "green", (-299, -200)),
            ("Moderate Risk", "yellow", (-199, 100)),
            ("High Risk", "orange", (101, 250)),
            ("Very High Risk", "red", (251, float('inf')))
        ]
        risk_options = [f"{level} :large_{color}_circle:" for level, color, _ in risk_levels]
        risk_index = st.selectbox("Select Risk Level:", risk_options, key="sgp_plus_risk_level")
        selected_risk = next((r for r, c, _ in risk_levels if f"{r} :large_{c}_circle:" == risk_index), risk_levels[0])
        risk_level, color, (min_ods, max_odds) = selected_risk
        
        total_props = len(selected_games) * props_per_game
        st.write(f"✅ **Total Props Selected: {total_props} (Max: 24)**")

        if total_props > 24:
            st.error(f"🚨 Too many props selected! Max allowed: 24.")
        else:
            if st.button("Generate SGP+ Prediction"):
                num_props_total = props_per_game * len(selected_games)
                sgp_plus_result = fetch_sgp_builder(selected_games, num_props=num_props_total, min_odds=min_odds, max_odds=max_odds, multi_game=True)
                st.write(sgp_plus_result)

# Game Predictions
elif menu_option == "Game Predictions":
    st.header("📈 Moneyline, Spread & Over/Under Predictions")

    today_games = get_nba_games(datetime.date.today())
    tomorrow_games = get_nba_games(datetime.date.today() + datetime.timedelta(days=1))
    all_games = today_games + tomorrow_games
    game_labels = [f"{game['home_team']} vs {game['away_team']}" for game in all_games]
    selected_labels = st.multiselect("Select Games for Predictions:", game_labels)
    selected_games = [g for g in all_games if f"{g['home_team']} vs {g['away_team']}" in selected_labels]

    if len(selected_games) == 0:
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
