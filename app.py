import streamlit as st
from utils import fetch_games, fetch_props, fetch_ml_spread_ou, fetch_player_data

# Title
st.title("MVP Tool - NBA Betting Analysis")

# Sidebar for game selection
selected_games = st.sidebar.multiselect("Select Games:", fetch_games())

# Toggle for ML/Spread/O/U predictions
toggle_ml_spread_ou = st.sidebar.checkbox("Include ML/Spread/O/U Predictions")

# Toggle for Player Props
toggle_player_props = st.sidebar.checkbox("Include Player Props")

# Risk Level Selection
risk_level = st.sidebar.radio("Select Risk Level:", ["Very Safe", "Safe", "Moderate Risk", "High Risk", "Very High Risk"])

# Number of Props Per Game
num_props = st.sidebar.slider("Number of Props Per Game", 1, 8, 4)

# SGP & SGP+ Toggle
toggle_sgp = st.sidebar.checkbox("Same Game Parlay (SGP)")
toggle_sgp_plus = st.sidebar.checkbox("Multi-Game SGP+ (Includes multiple games)")

# Run Predictions
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

# Player Search Feature
player_name = st.text_input("Search Player Stats & Best Bets:")
if player_name:
    player_data = fetch_player_data(player_name)
    if player_data:
        st.write(f"### Stats & Best Bets for {player_name}")
        st.write(player_data)
    else:
        st.error("Player not found or no available data.")
