import streamlit as st
import datetime
import math
from utils import (
    fetch_player_data, fetch_best_props,
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends,
    fetch_all_players, get_nba_games
)
from nba_api.stats.static import teams

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# Sidebar Navigation
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.selectbox("Select a Section:", ["Player Search", "Same Game Parlay", "SGP+", "Game Predictions"])

# Player Search
if menu_option == "Player Search":
    st.header("🔍 Player Search & Prop Analysis")

    all_players = fetch_all_players()
    last_name_mapping = {p.split()[-1].lower(): p for p in all_players}
    nickname_mapping = {
        "steph curry": "Stephen Curry",
        "bron": "LeBron James",
        "kd": "Kevin Durant",
        "ad": "Anthony Davis",
        "cp3": "Chris Paul",
        "joker": "Nikola Jokic",
        "the beard": "James Harden",
        "dame": "Damian Lillard",
        "klay": "Klay Thompson",
        "tatum": "Jayson Tatum",
        "giannis": "Giannis Antetokounmpo"
    }

    player_name = st.text_input("Enter Player Name, Last Name, or Nickname", key="player_search")
    if player_name:
        player_name_lower = player_name.lower()
        if player_name_lower in nickname_mapping:
            player_name = nickname_mapping[player_name_lower]
        elif player_name_lower in last_name_mapping:
            player_name = last_name_mapping[player_name_lower]

        selected_team = st.selectbox("Select Opponent for H2H Analysis (Optional)", ["None"] + [t["full_name"] for t in teams.get_teams()])
        selected_team = None if selected_team == "None" else selected_team

        player_stats, h2h_stats = fetch_player_data(player_name, selected_team)

        if player_stats:
            st.subheader(f"📈 {player_name} Stats - Last 5, 10, 15 Games")
            st.write(player_stats)
            if h2h_stats:
                st.subheader(f"🤼 H2H Stats vs {selected_team}")
                st.write(h2h_stats)
        else:
            st.error(f"🚨 No stats found for {player_name}. Check name spelling or API availability.")

# Same Game Parlay
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
