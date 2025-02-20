import time
import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.endpoints import playergamelog, scoreboard
import streamlit as st  # ✅ UI for game & player selection
import requests  # ✅ For sportsbook API integration

# ✅ 1️⃣ Fetch NBA Games (Today or Tomorrow)
def fetch_games(day_offset=0, max_retries=3):
    """
    Fetches NBA games for today (default) or tomorrow (if day_offset=1).
    Returns a list of tuples with (game_id, matchup).
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

        if "scoreboard" not in games_data or "games" not in games_data["scoreboard"]:
            return []

        games_list = []
        for game in games_data["scoreboard"]["games"]:  
            matchup = f"{game['awayTeam']['teamName']} vs {game['homeTeam']['teamName']}"
            games_list.append((game["gameId"], matchup))  # Store game ID & matchup

        return games_list if games_list else []

    except Exception as e:
        return [f"API Error: {str(e)}"]


# ✅ 2️⃣ Fetch Real-Time Player Stats (Last 10 Games & Previous Matchups)
def get_recent_player_stats(player_id, opponent_abbreviation):
    """
    Fetches last 10 games stats for a player and previous matchups vs. today's opponent.
    """
    try:
        season = "2023-24"  # Ensure current season data
        game_log = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
        last_10_games = game_log.head(10)  # Get last 10 games
        
        # Filter games vs. today's opponent
        prev_matchups = game_log[game_log["MATCHUP"].str.contains(opponent_abbreviation, na=False)]
        
        return last_10_games, prev_matchups

    except Exception as e:
        return f"Failed to fetch recent stats for player ID {player_id}: {str(e)}"


# ✅ 3️⃣ Fetch Live Moneyline, Spread, and Over/Under Odds
def fetch_ml_spread_ou(game_id):
    """
    Fetches real-time Moneyline, Spread, and Over/Under odds from sportsbooks.
    """
    try:
        url = f"https://api.sportsbook.com/v1/odds/nba/{game_id}"  # Replace with real sportsbook API
        response = requests.get(url)
        
        # ✅ Check if request was successful
        if response.status_code != 200:
            return f"Error: Failed to fetch odds. Status Code: {response.status_code}"

        data = response.json()

        # ✅ Ensure the JSON response has expected fields
        if "odds" not in data:
            return f"Error: Unexpected JSON format - missing 'odds' key"

        return data["odds"]

    except Exception as e:
        return f"Error fetching ML/Spread/O/U odds: {str(e)}"


# ✅ 4️⃣ Fetch Live Player Prop Bets
def fetch_props(player_name):
    """
    Fetches available player props (points, assists, rebounds, etc.) from sportsbooks.
    """
    try:
        url = f"https://api.sportsbook.com/v1/player-props/nba/{player_name}"  # Replace with real API
        response = requests.get(url)

        # ✅ Check if request was successful
        if response.status_code != 200:
            return f"Error: Failed to fetch props. Status Code: {response.status_code}"

        data = response.json()

        # ✅ Ensure the JSON response has expected fields
        if "props" not in data:
            return f"Error: Unexpected JSON format - missing 'props' key"

        return data["props"]

    except Exception as e:
        return f"Error fetching props for {player_name}: {str(e)}"


# ✅ 5️⃣ Streamlit UI for Game Selection (Dropdown + Radio Buttons)
def show_game_selection_ui():
    """
    Displays a Streamlit UI for selecting today's or tomorrow's NBA games.
    """
    st.title("NBA Games Schedule")

    # **Radio Buttons for Today/Tomorrow Selection**
    selected_option = st.radio("Select Date:", ["Today's Games", "Tomorrow's Games"])

    # **Fetch Games Based on Selection**
    games = fetch_games(0) if selected_option == "Today's Games" else fetch_games(1)

    # **Dropdown for Selecting a Game**
    if games:
        game_options = {matchup: game_id for game_id, matchup in games}
        selected_game = st.selectbox("Choose a game:", list(game_options.keys()))

        st.write(f"**You selected:** {selected_game}")

        # Fetch betting odds for selected game
        st.subheader("Current Betting Lines (ML, Spread, O/U):")
        odds = fetch_ml_spread_ou(game_options[selected_game])
        st.write(odds)

    else:
        st.write("No games scheduled for this date.")


# ✅ 6️⃣ Streamlit UI for Player Search (Last 10 Games + Previous Matchups)
def show_player_search_ui():
    """
    Displays a Streamlit UI for searching NBA player stats and props.
    """
    st.title("NBA Player Search & Props")

    player_name = st.text_input("Enter Player Name:")

    # Fetch today's games so we can identify matchups
    today_games = fetch_games(0)
    opponent_abbreviation = None

    if player_name:
        from nba_api.stats.static import players
        player_dict = players.get_players()
        player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)

        if player:
            player_id = player["id"]

            # Try to find the player's matchup from today's games
            for game_id, game in today_games:
                teams = game.split(" vs ")
                if any(player_name.split()[-1] in team for team in teams):  # Check if player is on one of the teams
                    opponent_abbreviation = teams[1] if player_name.split()[-1] in teams[0] else teams[0]

            # Fetch player stats
            last_10_games, prev_matchups = get_recent_player_stats(player_id, opponent_abbreviation)

            # Display last 10 games
            st.subheader(f"Last 10 Games for {player_name}")
            if isinstance(last_10_games, pd.DataFrame):
                st.dataframe(last_10_games)
            else:
                st.write(last_10_games)

            # Display previous matchups vs. today's opponent
            st.subheader(f"Previous Matchups vs. {opponent_abbreviation}")
            if isinstance(prev_matchups, pd.DataFrame) and not prev_matchups.empty:
                st.dataframe(prev_matchups)
            else:
                st.write(f"No previous matchups against {opponent_abbreviation} this season.")

        else:
            st.write(f"Error: Player '{player_name}' not found.")

        # Display player props
        st.subheader(f"Player Prop Bets for {player_name}")
        props = fetch_props(player_name)
        st.write(props)


# ✅ Run Streamlit UI
if __name__ == "__main__":
    st.sidebar.title("NBA Betting Tool")
    page = st.sidebar.selectbox("Choose a Page:", ["Game Schedule", "Player Search"])
    if page == "Game Schedule":
        show_game_selection_ui()
    elif page == "Player Search":
        show_player_search_ui()
