import requests
import json
import streamlit as st
from datetime import datetime, timedelta
from nba_api.stats.endpoints import ScoreboardV2, commonplayerinfo, playergamelogs
from nba_api.stats.endpoints import leaguedashplayerstats

# ✅ Fetch NBA games for today or tomorrow (REAL DATA)
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime, timedelta

# ✅ Fetch Games for Today & Tomorrow
def fetch_games():
    try:
        # Set the current date
        today = datetime.today()
        today_str = today.strftime("%Y-%m-%d")
        tomorrow = today + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")

        # ✅ Fetch NBA schedule using real-time API
        scoreboard = scoreboardv2.ScoreboardV2(day_offset=0)  # Today’s games
        games_today = scoreboard.get_dict()["resultSets"][0]["rowSet"]

        scoreboard_tomorrow = scoreboardv2.ScoreboardV2(day_offset=1)  # Tomorrow’s games
        games_tomorrow = scoreboard_tomorrow.get_dict()["resultSets"][0]["rowSet"]

        # ✅ Process game data into "TEAM vs TEAM" format
        def format_games(games):
            return [f"{game[5]} vs {game[6]}" for game in games]  # Team Abbreviations

        return {
            "today": format_games(games_today) if games_today else ["No Games Today"],
            "tomorrow": format_games(games_tomorrow) if games_tomorrow else ["No Games Tomorrow"]
        }

    except Exception as e:
        return {"error": f"Failed to fetch games: {str(e)}"}

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]

# ✅ Fetch real player data (box scores, stats, trends)


# ✅ Fetch player prop odds from sportsbooks (FanDuel, DraftKings, BetMGM)
def fetch_props(game):
    try:
        sportsbook_api_url = f"https://api.sportsbook.com/props?game={game}"
        response = requests.get(sportsbook_api_url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to fetch player props"}
    except Exception as e:
        return {"error": f"Error fetching player props: {e}"}

# ✅ Fetch Moneyline, Spread, and Over/Under odds from sportsbooks
def fetch_ml_spread_ou(game):
    try:
        sportsbook_api_url = f"https://api.sportsbook.com/ml_spread_ou?game={game}"
        response = requests.get(sportsbook_api_url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to fetch ML, Spread, and O/U odds"}
    except Exception as e:
        return {"error": f"Error fetching ML, Spread, and O/U odds: {e}"}
