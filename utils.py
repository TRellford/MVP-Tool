import requests
from nba_api.stats.endpoints import scoreboard, commonplayerinfo, playergamelogs
from nba_api.stats.static import players
from datetime import datetime, timedelta

# ✅ Fetch Today's NBA Games

def fetch_games(day_offset=0):
    """
    Fetches NBA games for today (default) or tomorrow (if day_offset=1).
    """
    try:
        # Get the selected date
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

        # Fetch games using NBA API's Scoreboard
        games_data = scoreboard.Scoreboard(game_date=selected_date).get_dict()

        if "games" not in games_data:
            return ["No games available or API issue. Try again later."]

        games_list = []
        for game in games_data["games"]:  # Correct key usage
            matchup = f"{game['awayTeam']['teamName']} vs {game['homeTeam']['teamName']}"
            games_list.append(matchup)

        return games_list if games_list else ["No Games Scheduled"]

    except Exception as e:
        return [f"API Error: {str(e)}"]

# Example Usage:
# Call fetch_games(0) for today’s games, fetch_games(1) for tomorrow’s games.
games_today = fetch_games(0)
games_tomorrow = fetch_games(1)

print("Today's Games:", games_today)
print("Tomorrow's Games:", games_tomorrow)
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
    """Fetch player profile & last 10 games data."""
    try:
        # ✅ Get player ID
        from nba_api.stats.static import players
        player_dict = players.get_players()
        player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)
        
        if not player:
            return {"error": f"Player '{player_name}' not found."}

        player_id = player["id"]

        # ✅ Get player profile & stats
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_dict()
        player_stats = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable="2023-24").get_dict()

        # ✅ Extract profile data
        profile = player_info["resultSets"][0]["rowSet"][0]

        # ✅ Convert last 10 games into a readable format
        stats_df = pd.DataFrame(player_stats["resultSets"][0]["rowSet"], 
                                columns=player_stats["resultSets"][0]["headers"])

        # ✅ Ensure all numeric data is converted to **strings** to prevent ArrowTypeError
        stats_df = stats_df.applymap(lambda x: str(x) if isinstance(x, (int, float)) else x)

        player_data = {
            "name": profile[3],  # "LeBron James"
            "team": profile[19],  # "Lakers"
            "position": profile[14],  # "Forward"
            "height": profile[11],  # "6-9"
            "weight": profile[12],  # "250"
            "last_10_games": stats_df.to_dict(orient="records")  # Ensure proper format
        }

        return player_data

    except Exception as e:
        return {"error": f"Failed to fetch data for {player_name}: {str(e)}"}
