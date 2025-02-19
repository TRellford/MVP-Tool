from nba_api.stats.endpoints import ScoreboardV2, commonplayerinfo, playergamelogs
import requests

def fetch_games(date_choice):
    try:
        response = ScoreboardV2().get_dict()
        games = response.get("gameHeader", [])

        if not games:
            return ["No Games Available"]

        game_list = []
        for game in games:
            away_team = game.get("visitorTeam", {}).get("teamTricode", "N/A")
            home_team = game.get("homeTeam", {}).get("teamTricode", "N/A")
            game_list.append(f"{away_team} vs {home_team}")

        return game_list

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]

# Fetch Props (Player Betting Lines)
def fetch_props(selected_games, confidence, risk, sgp, sgp_plus):
    try:
        # Simulated API response
        props = [
            {"Player": "LeBron James", "Prop": "Over 7.5 Assists", "Odds": "-130", "Confidence": 92, "Risk": "Safe"},
            {"Player": "Nikola Jokic", "Prop": "Over 11.5 Rebounds", "Odds": "-140", "Confidence": 88, "Risk": "Safe"},
            {"Player": "Jayson Tatum", "Prop": "Over 2.5 Threes", "Odds": "+110", "Confidence": 90, "Risk": "Moderate"},
        ]
        return props

    except Exception as e:
        print(f"Error fetching props: {e}")
        return ["Error fetching props"]

# Fetch ML, Spread, and Over/Under
def fetch_ml_spread_ou(selected_games, confidence):
    try:
        ml_spread_ou = [
            {"Game": "LAL vs. DEN", "Moneyline": "Lakers +180", "Spread": "LAL +5.5 (-110)", "Total": "O 221.5 (-110)", "Confidence": 89},
            {"Game": "BOS vs. MIA", "Moneyline": "Celtics -220", "Spread": "BOS -6.5 (-105)", "Total": "U 215.5 (-115)", "Confidence": 91},
        ]
        return ml_spread_ou

    except Exception as e:
        print(f"Error fetching ML/Spread/O/U: {e}")
        return ["Error fetching ML/Spread/O/U"]

# Fetch Player Data (Search Feature)
def fetch_player_data(player_name):
    try:
        player_info = commonplayerinfo.CommonPlayerInfo(player_name).get_dict()
        stats = playergamelogs.PlayerGameLogs(player_name).get_dict()

        return {
            "Team": player_info.get("teamFullName", "N/A"),
            "Last 5 Games": stats.get("games", [])[:5],  # Display last 5 games
            "Best Bets": ["Over 20.5 Points (-110)", "Over 7.5 Assists (-120)"]  # Simulated data
        }

    except Exception as e:
        print(f"Error fetching player data: {e}")
        return None
