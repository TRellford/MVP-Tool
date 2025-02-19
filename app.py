import streamlit as st
from utils import fetch_games, fetch_props, fetch_ml_spread_ou, fetch_player_data

# Title
st.title("MVP Tool - NBA Betting Analysis")

# **Game Date Selection**
game_date = st.sidebar.radio("Select Game Date:", ["Today", "Tomorrow"])

# **Fetch Games Based on Selected Date**
selected_games = st.sidebar.multiselect("Select Games:", fetch_games(game_date))

# **Toggles for ML/Spread/O/U & Player Props**
toggle_ml_spread_ou = st.sidebar.checkbox("Include ML/Spread/O/U Predictions")
toggle_player_props = st.sidebar.checkbox("Include Player Props")

# **Risk Level Selection**
risk_level = st.sidebar.radio("Select Risk Level:", ["Very Safe", "Safe", "Moderate Risk", "High Risk", "Very High Risk"])

# **Number of Props Per Game**
num_props = st.sidebar.slider("Number of Props Per Game", 1, 8, 4)

# **SGP & SGP+ Toggle**
toggle_sgp = st.sidebar.checkbox("Same Game Parlay (SGP)")
toggle_sgp_plus = st.sidebar.checkbox("Multi-Game SGP+ (Includes multiple games)")

# **Player Search Feature**
st.sidebar.subheader("🔍 Player Search")
player_name = st.sidebar.text_input("Enter Player Name:")
if player_name:
    player_data = fetch_player_data(player_name)
    if player_data:
        st.write(f"### {player_name}'s Stats & Best Bets")
        st.table(player_data)
    else:
        st.error("Player not found or no available data.")

# **Game Predictions & Player Props**
if st.button("Get Predictions"):
    if not selected_games:
        st.error("Please select at least one game.")
    else:
        st.subheader("Game Predictions & Player Props")

        # Moneyline, Spread, and O/U Predictions
        if toggle_ml_spread_ou:
            ml_spread_ou_results = fetch_ml_spread_ou(selected_games)
            st.write("### Moneyline, Spread & O/U Predictions")
            st.table(ml_spread_ou_results)

        # Player Props
        if toggle_player_props:
            st.write("### Top Player Props")
            for game in selected_games:
                props = fetch_props(game, num_props, risk_level)
                st.write(f"#### {game}")
                st.table(props)
