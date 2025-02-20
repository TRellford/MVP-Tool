import requests
import json
import streamlit as st
from datetime import datetime, timedelta
from nba_api.stats.endpoints import ScoreboardV2, commonplayerinfo, playergamelogs
from nba_api.stats.endpoints import leaguedashplayerstats

# ✅ Fetch NBA games for today or tomorrow (REAL DATA)
from nba_api.stats.endpoints import ScoreboardV2
from datetime import datetime, timedelta

# ✅ Fetch NBA games for today or tomorrow (REAL DATA)
def fetch_games(date_choice="today"):
    try:
        # Set the correct date for filtering games
        target_date = datetime.now().strftime("%Y-%m-%d") if date_choice == "today" else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Fetch the scoreboard data
        scoreboard = ScoreboardV2(dayOffset=0 if date_choice == "today" else 1)
        games = scoreboard.get_dict()["resultSets"][0]["rowSet"]

        if not games:
            return [f"No Games Available for {target_date}"]

        game_list = []
        for game in games:
            home_team = game[6]  # Home team abbreviation (e.g., "LAL")
            away_team = game[7]  # Away team abbreviation (e.g., "BOS")
            game_date = game[0]  # Date of the game
            
            if game_date == target_date:  # Ensure correct date filtering
                game_info = f"{away_team} vs {home_team} ({target_date})"
                game_list.append(game_info)

        return game_list

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]

# ✅ Fetch real player data (box scores, stats, trends)
def fetch_player_data(player_name):
    try:
        player_info = commonplayerinfo.CommonPlayerInfo(player_name=player_name).get_dict()
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(season="2023-24").get_dict()

        return {
            "player_info": player_info,
            "player_stats": player_stats
        }
    except Exception as e:
        return {"error": f"Failed to fetch data for {player_name}: {e}"}

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
