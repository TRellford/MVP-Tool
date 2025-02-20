import time
import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, scoreboard
import streamlit as st  # ✅ UI Support for Today/Tomorrow Selection

# 1️⃣ Fetch NBA Games (Today or Tomorrow)
def fetch_games(day_offset=0, max_retries=3):
    """
    Fetches NBA games for today (default) or tomorrow (if day_offset=1).
    """
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

        for attempt in range(max_retries):
            try:
                games_data = scoreboard.Scoreboard(game_date=selected_date).get_dict()
                break  # Exit loop if request is successful
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Retry with a short delay
                else:
                    return [f"API Error after {max_retries} retries: {str(e)}"]

        if "games" not in games_data:
            return ["No games available or API issue. Try again later."]

        games_list = []
        for game in games_data["games"]:  # Correct key usage
            matchup = f"{game['awayTeam']['teamName']} vs {game['homeTeam']['teamName']}"
            games_list.append(matchup)

        return games_list if games_list else ["No Games Scheduled"]

    except Exception as e:
        return [f"API Error: {str(e)}"]


# 2️⃣ Universal Player Search Function
def get_player_stats(player_name):
    """
    Fetches career stats for any NBA player.
    """
    try:
        # Find player ID by searching for the player's name
        player_dict = players.get_players()
        player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)
        
        if not player:
            return f"Error: Player '{player_name}' not found."

        player_id = player["id"]
        
        # Fetch career stats
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]

        # Convert to DataFrame if it's not already
        if not isinstance(career_stats, pd.DataFrame):
            career_stats = pd.DataFrame(career_stats)

        return career_stats

    except Exception as e:
        return f"Failed to fetch data for {player_name}: {str(e)}"


# 3️⃣ Fetch Moneyline (ML), Spread, and Over/Under (O/U) Odds
def fetch_ml_spread_ou(game_id):
    """
    Fetches real-time Moneyline, Spread, and Over/Under odds for a given NBA game.
    """
    try:
        # 🔥 Placeholder API Call (Replace with actual sportsbook API)
        # Example of data structure returned by sportsbook API
        betting_data = {
            "Moneyline": {"Home": "-130", "Away": "+110"},
            "Spread": {"Home": "-3.5 (-110)", "Away": "+3.5 (-110)"},
            "Over/Under": {"Over": "225.5 (-110)", "Under": "225.5 (-110)"}
        }
        return betting_data

    except Exception as e:
        return f"Error fetching ML/Spread/O/U for Game ID {game_id}: {str(e)}"


# 4️⃣ Fetch Player Props (Points, Assists, Rebounds, etc.)
def fetch_props(player_name):
    """
    Fetches available player props (points, assists, rebounds, etc.) from sportsbooks.
    """
    try:
        # 🔥 Placeholder Data - Replace with a real sportsbook API
        player_props = {
            "Points": "Over/Under 24.5 (-110)",
            "Assists": "Over/Under 5.5 (-105)",
            "Rebounds": "Over/Under 8.5 (-115)"
        }
        return player_props
    except Exception as e:
        return f"Error fetching props for {player_name}: {str(e)}"


# 5️⃣ Streamlit UI for Today/Tomorrow Selection
def show_game_selection_ui():
    """
    Displays a Streamlit UI for selecting today's or tomorrow's NBA games.
    """
    st.title("NBA Games Schedule")

    # **Create Radio Buttons for Game Selection**
    selected_option = st.radio("Select Date:", ["Today's Games", "Tomorrow's Games"])

    # **Fetch Games Based on User Selection**
    if selected_option == "Today's Games":
        games = fetch_games(0)
    else:
        games = fetch_games(1)

    # **Display Games in Streamlit**
    if isinstance(games, list):
        for game in games:
            st.write(game)
    else:
        st.write("No games found.")


# Example Usage (Testing)
if __name__ == "__main__":
    # ✅ Test Game Fetching
    print("Today's Games:", fetch_games(0))
    print("Tomorrow's Games:", fetch_games(1))

    # ✅ Test Player Search
    player_name = input("Enter the player's name: ")
    print(get_player_stats(player_name))

    # ✅ Fetch ML, Spread, O/U for a sample game
    sample_game_id = "12345"  # Replace with an actual game ID
    print(fetch_ml_spread_ou(sample_game_id))

    # ✅ Fetch Player Props
    print(fetch_props(player_name))

    # ✅ Run Streamlit UI for Game Selection
    show_game_selection_ui()
