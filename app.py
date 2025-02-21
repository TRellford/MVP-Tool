import streamlit as st
from utils import fetch_games, fetch_player_data, fetch_player_stats

def main():
    st.title("🏀 NBA Betting Insights Tool - Fully Updated")

    # ✅ Radio buttons for Today/Tomorrow selection
    selected_option = st.radio("Select Date:", ["Today's Games", "Tomorrow's Games"], index=0)
    day_offset = 0 if selected_option == "Today's Games" else 1

    # ✅ Fetch and display games
    games = fetch_games(day_offset)
    if games and "No games available" not in games:
        selected_games = st.multiselect("Choose games:", games)  # ✅ Multi-game selection
    else:
        st.write("No games available for the selected date.")
        return

# ✅ Player Search
st.subheader("🔍 Search for a Player")
player_name = st.text_input("Enter player name:")
if player_name:
    player_data = fetch_player_data(player_name)
    if isinstance(player_data, dict) and "error" in player_data:
        st.warning(player_data["error"])  # ✅ Show warning if player isn't found
    else:
        st.json(player_data)  # ✅ Display player data properly

    # ✅ Player Props Selection (Season Averages)
    st.subheader("📊 Player Season Averages")
    if player_name and player_data and "error" not in player_data:
        player_id = player_data[0]["id"]
        
        for game in selected_games:
            st.subheader(f"📊 Stats for {game}")
            stats_data = fetch_player_stats(player_id)
            if stats_data:
                st.json(stats_data)
            else:
                st.write("No stats available for this player.")

if __name__ == "__main__":
    main()
