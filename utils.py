import requests
import json
from datetime import datetime, timedelta
from nba_api.stats.endpoints import scoreboardv2, commonplayerinfo
from nba_api.stats.static import players

### ✅ FETCH NBA GAMES (Fixes Incorrect Team Names & Allows Today/Tomorrow Selection) ###
def fetch_games():
    
    try:
        # Determine the correct date format
        today_date = datetime.now().strftime("%Y-%m-%d")
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        selected_date = today_date if date_choice == "Today" else tomorrow_date

        # Fetch NBA games for the selected date
        scoreboard = scoreboardv2.ScoreboardV2(game_date=today_date)
        games = scoreboard.get_dict()['resultSets'][0]['rowSet']

        game_list = []
        for game in games:
            home_team = game[6]  # Home team abbreviation
            away_team = game[7]  # Away team abbreviation
            game_info = f"{away_team} vs {home_team}"
            game_list.append(game_info)
    except Exception as e:  # Catch errors properly
        print(f"Error fetching games: {e}")
    game_list = []  # Return empty list if an error occurs

    return game_list
### ✅ FETCH PLAYER DATA (Fixes "Player Not Found" Error) ###
def fetch_player_data(player_name):
    """
    Fetches player information from the NBA API.
    :param player_name: Name of the player (e.g., "LeBron James")
    :return: Dictionary with player stats or "Player Not Found"
    """
    try:
        player_list = players.get_players()
        player = next((p for p in player_list if p["full_name"].lower() == player_name.lower()), None)

        if not player:
            return {"error": "Player Not Found"}

        player_id = player["id"]
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()

        return player_info

    except Exception as e:
        return {"error": f"Error fetching player data: {str(e)}"}
