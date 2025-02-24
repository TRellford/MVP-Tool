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
        
        # Number of props selection
        num_props = st.slider("Number of Props (1-8):", 1, 8, 1, key="sgp_num_props")
        
        # Risk level selection with colors
        risk_levels = [
            ("Very Safe", "blue", (-450, -300)),
            ("Safe", "green", (-299, -200)),
            ("Moderate Risk", "yellow", (-199, 100)),
            ("High Risk", "orange", (101, 250)),
            ("Very High Risk", "red", (251, float('inf')))
        ]
        risk_options = [f"{level} :large_{color}_circle:" for level, color, _ in risk_levels]
        risk_index = st.selectbox("Select Risk Level:", risk_options, key="sgp_risk_level")
        selected_risk = next((r for r, c, _ in risk_levels if f"{r} :large_{color}_circle:" == risk_index), risk_levels[0])
        risk_level, color, (min_odds, max_odds) = selected_risk
        
        if st.button("Generate SGP Prediction"):
            # Pass game, number of props, and risk range to fetch_sgp_builder
            sgp_result = fetch_sgp_builder(selected_game, num_props=num_props, min_odds=min_odds, max_odds=max_odds)
            st.write(sgp_result)
    else:
        st.warning("🚨 No NBA games found for the selected date.")

# SGP+
elif menu
