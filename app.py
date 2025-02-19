import streamlit as st
from utils import fetch_games, fetch_props, fetch_ml_spread_ou, fetch_player_data

# Title
st.title("🏀 Initial MVP Tool – NBA Betting Model")

# Sidebar - Select Games & Options
st.sidebar.header("Game & Bet Selection")
selected_date = st.sidebar.radio("Select Date:", ["Today", "Tomorrow"], index=0)
selected_games = st.sidebar.multiselect("Select Games:", fetch_games(selected_date))

# Toggle for Moneyline, Spread, Over/Under
bet_type = st.sidebar.radio("Bet Type:", ["Props", "ML/Spread/O/U", "Both"], index=0)

# Toggle for Same Game Parlay (SGP & SGP+)
sgp_toggle = st.sidebar.toggle("Same Game Parlay (SGP)")
sgp_plus_toggle = st.sidebar.toggle("SGP+ (Multiple Games)")

# Confidence Score & Risk Level
confidence_filter = st.sidebar.slider("Confidence Score Minimum:", 70, 100, 85)
risk_level = st.sidebar.radio("Risk Level:", ["Very Safe (🔵)", "Safe (🟢)", "Moderate (🟡)", "High (🟠)", "Very High (🔴)"], index=1)

# Fetch Predictions
if st.sidebar.button("Get Predictions"):
    if bet_type in ["Props", "Both"]:
        st.subheader("🎯 Top Player Prop Predictions")
        props = fetch_props(selected_games, confidence_filter, risk_level, sgp_toggle, sgp_plus_toggle)
        st.write(props)

    if bet_type in ["ML/Spread/O/U", "Both"]:
        st.subheader("📊 ML, Spread, Over/Under Predictions")
        ml_spread_ou = fetch_ml_spread_ou(selected_games, confidence_filter)
        st.write(ml_spread_ou)

# Player Search
st.sidebar.header("🔎 Player Search")
player_name = st.sidebar.text_input("Enter Player Name:")

if st.sidebar.button("Search Player"):
    player_data = fetch_player_data(player_name)
    if player_data:
        st.subheader(f"📊 Player Insights: {player_name}")
        st.write(player_data)
    else:
        st.error("Player not found or no available props.")
