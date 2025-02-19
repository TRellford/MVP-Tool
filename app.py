import streamlit as st
from utils import fetch_games, fetch_player_data

# 🎨 **Set UI Theme**
st.set_page_config(page_title="MVP Tool - NBA Betting Analysis", layout="wide")

### ✅ **SIDEBAR - DATE SELECTION & GAME DROPDOWN**
st.sidebar.title("Game Selection")

# Choose date: Today or Tomorrow
date_choice = st.sidebar.radio("Select Date", ["Today", "Tomorrow"])

# Fetch available games for selected date
selected_day = st.sidebar.radio("Select Date", ["Today", "Tomorrow"], key="date_selector")
day_offset = 0 if selected_day == "Today" else 1  # Set dayOffset based on selection
games = fetch_games(day_offset)  # Pass the correct day offset
# Ensure we handle errors and empty responses gracefully
if not games or "Error" in games[0] or "No Games Available" in games[0]:
    st.sidebar.warning(games[0])
    selected_games = []
else:
    selected_games = st.sidebar.multiselect("Select Games:", fetch_games())

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
st.write(selected_games if selected_games else "No Games Selected")
