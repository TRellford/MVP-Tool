import time
import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, leaguegamefinder, scoreboard

# 1️⃣ Fetch NBA Games (Today or Tomorrow)
def fetch_games(day_offset=0, max_retries=3):
    """
    Fetches NBA games for today (default) or tomorrow (if day_offset=1).
    """
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

        for attempt in range(max_retries):
            try:
                # Using Scoreboard instead of ScoreboardV2 to avoid redirect errors
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


# 3️⃣ Helper Function to Display DataFrames (For Google Colab or UI Display)
def display_player_stats(player_name):
    """
    Fetches and displays player stats in a structured format.
    """
    player_stats = get_player_stats(player_name)

    if isinstance(player_stats, pd.DataFrame):
        import ace_tools as tools
        tools.display_dataframe_to_user(name=f"{player_name} Stats", dataframe=player_stats)
    else:
        print(player_stats)  # Prints error messages


# Example Usage (Testing)
if __name__ == "__main__":
    # Test Game Fetching
    print("Today's Games:", fetch_games(0))
    print("Tomorrow's Games:", fetch_games(1))

    # Test Player Search
    player_name = input("Enter the player's name: ")  # User inputs any player
    display_player_stats(player_name)
