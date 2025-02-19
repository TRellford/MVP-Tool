import requests
import json
from datetime import datetime, timedelta
from nba_api.stats.endpoints import scoreboardv2, commonplayerinfo
from nba_api.stats.static import players

### ✅ FETCH NBA GAMES (Fixes Incorrect Team Names & Allows Today/Tomorrow Selection) ###
def fetch_games(day_offset=0):  # Allow an optional argument
    try:
        scoreboard = ScoreboardV2(dayOffset=day_offset)  # Use the optional argument
        games = scoreboard.get_dict()["resultSets"][0]["rowSet"]
        game_list = [f"{game[6]} vs {game[7]}" for game in games]  # 6 & 7 are team abbreviations
        return game_list
    except Exception as e:
        print(f"Error fetching games: {e}")
        return []  # Return an empty list if an error occurs
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
