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
        st.write(f"🎯 Selected Game: {selected_game_label}")
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
        props_per_game = st.slider(f"Choose Props Per Game (Max {max_props_per_game}):", 2, max_props_per_game)

        total_props = len(selected_games) * props_per_game
        st.write(f"✅ **Total Props Selected: {total_props} (Max: 24)**")

        if total_props > 24:
            st.error(f"🚨 Too many props selected! Max allowed: 24.")
        else:
            if st.button("Generate SGP+"):
                sgp_plus_result = fetch_sgp_builder(selected_games, props_per_game, multi_game=True)
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
                    st.write(pred)

    st.header("💰 Sharp Money & Line Movement Tracker")
    if len(selected_games) > 0 and st.button("Check Betting Trends"):
        sharp_trends = fetch_sharp_money_trends(selected_games)
        st.write(sharp_trends)
