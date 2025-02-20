import streamlit as st
from utils import (
    fetch_todays_games,
    fetch_player_data,
    fetch_game_predictions,
    fetch_player_props,
    fetch_betting_edges,
)

# Streamlit App Title
st.title("MVP Tool - Live NBA Betting Analytics")

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Game Predictions", "Player Props", "Player Search", "Betting Edges"])

# ✅ Game Predictions Section
if page == "Game Predictions":
    st.header("🏀 Game Predictions")
    st.write("Fetching real-time game predictions...")

    games = fetch_todays_games()
    if games:
        selected_game = st.selectbox("Select a Game", games)
        if st.button("Get Predictions"):
            predictions = fetch_game_predictions(selected_game)
            st.write(predictions)
    else:
        st.warning("No games available today.")

# ✅ Player Props Section
elif page == "Player Props":
    st.header("📊 Player Props")
    st.write("Select a game to view high-confidence player props.")

    games = fetch_todays_games()
    if games:
        selected_game = st.selectbox("Select a Game", games)
        num_props = st.slider("Number of Props", 1, 8, 3)
        risk_level = st.selectbox("Select Risk Level", ["Very Safe", "Safe", "Moderate", "High Risk"])

        if st.button("Get Props"):
            props = fetch_player_props(selected_game, num_props, risk_level)
            st.write(props)
    else:
        st.warning("No games available today.")

# ✅ Player Search Section
elif page == "Player Search":
    st.header("🔎 Search for a Player")
    player_name = st.text_input("Enter a player's name")

    if st.button("Search"):
        player_info = fetch_player_data(player_name)
        if "error" in player_info:
            st.error(player_info["error"])
        else:
            st.write(player_info)

# ✅ Betting Edges Section
elif page == "Betting Edges":
    st.header("💰 Best Betting Edges")
    st.write("Finding high-value bets with line discrepancies...")

    if st.button("Get Betting Edges"):
        betting_edges = fetch_betting_edges()
        st.write(betting_edges)

st.sidebar.text("MVP Tool - Live NBA Data")
