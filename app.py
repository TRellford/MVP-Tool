import streamlit as st
from utils import fetch_games, fetch_props, fetch_ml_spread_ou, fetch_player_data

st.set_page_config(page_title="MVP Tool", layout="wide")

# UI Layout
st.title("MVP Sports Betting Tool 🚀")
st.sidebar.header("Game Selection")

# Toggle Features
sgp_toggle = st.sidebar.checkbox("Enable Same Game Parlay (SGP)")
sgp_plus_toggle = st.sidebar.checkbox("Enable SGP+ (Multiple Games)")
ml_toggle = st.sidebar.checkbox("Include Moneyline/Spread/O/U")

# Game Selection
selected_games = st.sidebar.multiselect("Select Games:", fetch_games())

# Prop Selection
prop_count = st.sidebar.slider("Number of Props Per Game", 1, 8, 4)

# Risk Level Selection
risk_level = st.sidebar.selectbox("Select Risk Level:", ["Very Safe", "Safe", "Moderate", "High Risk"])

# Fetch Predictions
if st.sidebar.button("Get Predictions"):
    if ml_toggle:
        ml_results = fetch_ml_spread_ou(selected_games)
        st.subheader("Moneyline, Spread & Over/Under Predictions")
        st.table(ml_results)

    if selected_games:
        props = fetch_props(selected_games, prop_count, risk_level, sgp_toggle, sgp_plus_toggle)
        st.subheader("Top Player Props")
        st.table(props)

# Player Search
st.sidebar.header("Player Search")
player_name = st.sidebar.text_input("Enter Player Name")
if st.sidebar.button("Search"):
    player_info = fetch_player_data(player_name)
    st.subheader(f"Player Analysis: {player_name}")
    st.table(player_info)
