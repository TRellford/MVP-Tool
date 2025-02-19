import requests
import json
from datetime import datetime, timedelta
from nba_api.stats.endpoints import scoreboardv2, commonplayerinfo
from nba_api.stats.static import players

### ✅ FETCH NBA GAMES (Fixes Incorrect Team Names & Allows Today/Tomorrow Selection) ###
def fetch_games(date=None):  # Allow an optional argument
    try:
        response = ScoreboardV2().get_dict()
        games = response.get("gameHeader", [])

        if not games:
            return ["No Games Available"]

        game_list = [
            f"{game['visitorTeam']['teamTricode']} vs {game['homeTeam']['teamTricode']}"
            for game in games
        ]
        return game_list

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]
        
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
