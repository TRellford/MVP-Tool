import streamlit as st
from utils import fetch_games, fetch_sportsbook_odds, fetch_player_props  # ✅ Ensure proper imports

def main():
    st.title("🏀 NBA Betting Insights Tool - Fixed Version")

    # ✅ Radio buttons for Today/Tomorrow selection
    selected_option = st.radio("Select Date:", ["Today's Games", "Tomorrow's Games"], index=0)
    day_offset = 0 if selected_option == "Today's Games" else 1

    # ✅ Fetch and display games
    games = fetch_games(day_offset)
    if games and "No games available" not in games:
        selected_game = st.selectbox("Choose a game:", games)
    else:
        st.write("No games available for the selected date.")
        return

    # ✅ Display sportsbook odds (Correcting API response format)
    st.subheader("📊 Sportsbook Odds (ML, Spread, O/U)")
    odds_data = fetch_sportsbook_odds(selected_game)
    if odds_data and "error" not in odds_data:
        st.json(odds_data)  # ✅ Use `st.json()` instead of `st.write()` to format API data correctly
    else:
        st.write("No odds available.")

    # ✅ Display player props (Fixing extra code display)
    st.subheader("🎯 Player Props")
    props_data = fetch_player_props(selected_game)
    if props_data and "error" not in props_data:
        st.json(props_data)  # ✅ Properly format player props
    else:
        st.write("No player props available.")

if __name__ == "__main__":
    main()
