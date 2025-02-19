import streamlit as st
from utils import fetch_games, fetch_player_data

# 🎨 **Set UI Theme**
st.set_page_config(page_title="MVP Tool - NBA Betting Analysis", layout="wide")

### ✅ **SIDEBAR - DATE SELECTION & GAME DROPDOWN**
st.sidebar.title("Game Selection")

# Choose date: Today or Tomorrow
date_choice = st.sidebar.radio("Select Date", ["Today", "Tomorrow"])

# Fetch available games for selected date
games = fetch_games(date_choice)

# Check if games were found before showing dropdown
if "Error" in games[0] or "No Games Found" in games:
    st.sidebar.warning(games[0])
else:
    selected_games = st.sidebar.multiselect("Select Games:", games)

### ✅ **SIDEBAR - PLAYER SEARCH**
st.sidebar.title("Player Search")
player_name = st.sidebar.text_input("Search Player (e.g., LeBron James)")
if player_name:
    player_data = fetch_player_data(player_name)
    if "error" in player_data:
        st.sidebar.warning(player_data["error"])
    else:
        st.sidebar.success(f"Showing stats for {player_name}")
        st.write(player_data)

### ✅ **DISPLAY SELECTED GAMES**
st.title("MVP Tool - NBA Betting Analysis")
st.write("### Selected Games:")
st.write(selected_games)
