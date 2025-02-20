import requests
from nba_api.stats.endpoints import scoreboardv2, commonplayerinfo, playergamelogs
from nba_api.stats.static import players
import datetime

# ✅ Fetch Today's NBA Games
def fetch_games():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        scoreboard = scoreboardv2.ScoreboardV2().get_dict()
        games = [
            f"{game[5]} vs {game[4]}"  # Home vs Away Team
            for game in scoreboard["resultSets"][0]["rowSet"]
        ]
        return games
    except Exception as e:
        return [f"Error fetching games: {e}"]

# ✅ Fetch Player Props for Selected Games
def fetch_props(selected_games, prop_count, risk_level, sgp_enabled, sgp_plus_enabled):
    props = []
    for game in selected_games:
        try:
            # ✅ Pull props based on live sportsbook data (FanDuel, DraftKings, BetMGM)
            game_data = requests.get(f"https://api.sportsbook.com/odds/{game}").json()
            
            # ✅ Sort props by confidence score & filter by risk level
            sorted_props = sorted(game_data, key=lambda x: x["confidence_score"], reverse=True)
            filtered_props = [
                prop for prop in sorted_props if risk_level in prop["risk_category"]
            ]
            
            # ✅ Add only selected props per game
            props.extend(filtered_props[:prop_count])
        except Exception as e:
            return [{"error": f"Failed to retrieve props for {game}: {e}"}]
    return props

# ✅ Fetch Moneyline, Spread, and Over/Under Predictions
def fetch_ml_spread_ou(selected_games):
    ml_data = []
    for game in selected_games:
        try:
            odds_data = requests.get(f"https://api.sportsbook.com/ml_spread_ou/{game}").json()
            ml_data.append(odds_data)
        except Exception as e:
            return [{"error": f"Failed to retrieve ML/Spread/O/U for {game}: {e}"}]
    return ml_data

# ✅ Fetch Player Data for Search Feature
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
        stats = player_stats["resultSets"][0]["rowSet"]

        return {
            "name": profile[3],
            "team": profile[19],
            "position": profile[14],
            "height": profile[11],
            "weight": profile[12],
            "last_10_games": stats[:10]
        }

    except Exception as e:
        return {"error": f"Failed to fetch data for {player_name}: {str(e)}"}
