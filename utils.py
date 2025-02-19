import requests
import json
from datetime import datetime, timedelta
from nba_api.stats.endpoints import scoreboardv2, commonplayerinfo
from nba_api.stats.static import players

### ✅ FETCH NBA GAMES (Fixes Incorrect Team Names & Allows Today/Tomorrow Selection) ###
def fetch_games(date_choice="Today"):
    """
    Fetches NBA games for today or tomorrow.
    :param date_choice: "Today" or "Tomorrow"
    :return: List of formatted games "AwayTeam vs HomeTeam"
    """
    try:
        # Fetch NBA schedule
        scoreboard = scoreboardv2.ScoreboardV2()
        games = scoreboard.get_dict()['resultSets'][0]['rowSet']

        game_list = []
        today_date = datetime.now().strftime("%Y-%m-%d")
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        for game in games:
            game_date = game[0]  # Extract game date
            away_team = game[7]  # Away team abbreviation
            home_team = game[6]  # Home team abbreviation

            if (date_choice == "Today" and game_date == today_date) or \
               (date_choice == "Tomorrow" and game_date == tomorrow_date):
                game_list.append(f"{away_team} vs {home_team}")

        return game_list if game_list else ["No Games Found"]

    except Exception as e:
        return [f"Error fetching games: {str(e)}"]

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
