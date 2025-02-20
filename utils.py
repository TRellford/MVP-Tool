import requests
from nba_api.stats.endpoints import commonplayerinfo, playergamelogs, scoreboard
from nba_api.stats.static import players
import datetime

# ✅ Fetch Today's NBA Games
def fetch_todays_games():
    try:
        today = datetime.datetime.today().strftime("%Y-%m-%d")
        scoreboard_data = scoreboard.Scoreboard(day_offset=0).get_dict()
        games = []

        for game in scoreboard_data["resultSets"][0]["rowSet"]:
            home_team = game[6]
            away_team = game[7]
            games.append(f"{away_team} vs {home_team}")

        return games

    except Exception as e:
        return {"error": f"Failed to fetch today's games: {str(e)}"}

# ✅ Fetch Player Data (Live)
def fetch_player_data(player_name):
    try:
        player_dict = players.get_players()
        player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)

        if not player:
            return {"error": f"Player '{player_name}' not found."}

        player_id = player["id"]
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
        player_stats = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable="2023-24").get_dict()

        profile = player_info["resultSets"][0]["rowSet"][0]
        stats = player_stats["resultSets"][0]["rowSet"][:10] if player_stats["resultSets"][0]["rowSet"] else []

        return {
            "name": profile[3],
            "team": profile[19],
            "position": profile[14],
            "height": profile[11],
            "weight": profile[12],
            "last_10_games": stats or "No games played this season"
        }

    except Exception as e:
        return {"error": f"Failed to fetch data for {player_name}: {str(e)}"}

# ✅ Fetch Game Predictions (Live)
def fetch_game_predictions(game):
    try:
        url = f"https://sportsdata.io/api/nba/predictions?game={game}"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch game predictions: {str(e)}"}

# ✅ Fetch Player Props (Live)
def fetch_player_props(game, num_props=3, risk_level="Safe"):
    try:
        url = f"https://sportsdata.io/api/nba/props?game={game}&num_props={num_props}&risk={risk_level}"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch player props: {str(e)}"}

# ✅ Fetch Best Betting Edges
def fetch_betting_edges():
    try:
        url = "https://sportsdata.io/api/nba/betting-edges"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch betting edges: {str(e)}"}
