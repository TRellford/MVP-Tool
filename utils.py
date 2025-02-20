import requests
import json
import streamlit as st
from datetime import datetime, timedelta
from nba_api.stats.endpoints import ScoreboardV2, commonplayerinfo, playergamelogs
from nba_api.stats.endpoints import leaguedashplayerstats

# ✅ Fetch NBA games for today or tomorrow (REAL DATA)
def fetch_games(date_choice="today"):
    try:
        # Set date filter
        target_date = datetime.now().strftime("%Y-%m-%d") if date_choice == "today" else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Fetch real NBA schedule from API
        response = ScoreboardV2(day_offset=0).get_dict()
        games = response.get("resultSets", [])[0].get("rowSet", [])

        if not games:
            return [f"No Games Available for {target_date}"]

        game_list = []
        for game in games:
            home_team = game[6]  # Home team abbreviation (e.g., "LAL")
            away_team = game[7]  # Away team abbreviation (e.g., "BOS")
            game_info = f"{away_team} vs {home_team} ({target_date})"
            game_list.append(game_info)

        return game_list

    except Exception as e:
        print(f"Error fetching games: {e}")
        return ["Error fetching games"]

# ✅ Fetch real player data (box scores, stats, trends)
def fetch_player_data(player_name):
    try:
        # Retrieve player info
        player_info = commonplayerinfo.CommonPlayerInfo(player_name=player_name).get_dict()
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(season="2023-24").get_dict()

        return {
            "player_info": player_info,
            "player_stats": player_stats
        }
    except Exception as e:
        return {"error": f"Failed to fetch data for {player_name}: {e}"}
