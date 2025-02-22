import requests
import os
import pandas as pd
import datetime
import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players

@st.cache_data(ttl=3600)

def get_games_by_date(target_date):
    """Fetch NBA games for a specific date and return matchups in 'Away Team at Home Team' format."""
    formatted_date = target_date.strftime("%Y-%m-%d")
    
    try:
        # Fetch scoreboard data for the given date
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        game_header_df = scoreboard.game_header.get_data_frame()
        line_score_df = scoreboard.line_score.get_data_frame()

        # Handle cases where no games are found
        if game_header_df.empty or line_score_df.empty:
            return ["⚠️ No games available or data not yet released."]

        # Create a mapping of TEAM_ID to 'CITY_NAME TEAM_NAME'
        team_id_to_name = {
            row['TEAM_ID']: f"{row['TEAM_CITY_NAME']} {row['TEAM_NAME']}"
            for _, row in line_score_df.iterrows()
            if pd.notna(row['TEAM_CITY_NAME']) and pd.notna(row['TEAM_NAME'])
        }

        # Construct game matchups using team names
        game_list = []
        for _, game in game_header_df.iterrows():
            home_team_id = game.get('HOME_TEAM_ID')
            visitor_team_id = game.get('VISITOR_TEAM_ID')
            
            home_team_name = team_id_to_name.get(home_team_id, "Unknown Home Team")
            visitor_team_name = team_id_to_name.get(visitor_team_id, "Unknown Visitor Team")
            
            matchup = f"{visitor_team_name} at {home_team_name}"
            game_list.append(matchup)

        return game_list if game_list else ["⚠️ No games scheduled for this date."]

    except Exception as e:
        return [f"❌ Error fetching games: {str(e)}"]

def fetch_all_players():
    """
    Fetches a list of all current NBA players dynamically from the API.
    This replaces the need for a hardcoded player list.
    """
    url = "https://www.balldontlie.io/api/v1/players"
    all_players = []
    page = 1

    while True:
        response = requests.get(f"{url}?per_page=100&page={page}")
        if response.status_code != 200:
            return []  # Return an empty list if the API fails

        data = response.json()
        players = data["data"]
        if not players:
            break  # Stop if no more players are found

        all_players.extend([player["first_name"] + " " + player["last_name"] for player in players])
        page += 1

    return sorted(all_players)  # Return sorted list for better UX

# --- Fetch Player Stats ---
@st.cache_data(ttl=600)
def fetch_player_data(player_name, trend_length):
    """Fetch player stats from NBA API."""
    player_dict = players.get_players()
    player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)

    if not player:
        return {"error": "Player not found."}

    player_id = player["id"]
    game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24")
    game_data = game_log.get_data_frames()[0].head(trend_length)

    return pd.DataFrame({
        "Game Date": pd.to_datetime(game_data["GAME_DATE"]),
        "Points": game_data["PTS"],
        "Rebounds": game_data["REB"],
        "Assists": game_data["AST"],
        "3PT Made": game_data["FG3M"]
    })

# --- Sharp Money & Line Movement Tracker ---
def fetch_sharp_money_trends(game_selection):
    """Fetches betting line movement & sharp money trends."""
    url = f"https://sportsdata.io/api/betting-trends?game={game_selection}"
    response = requests.get(url, headers={"Authorization": f"Bearer {os.getenv('BETTING_API_KEY')}"})

    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.text}"}

    data = response.json()
    return {
        "Public Bets %": data["public_bets"],
        "Sharp Money %": data["sharp_money"],
        "Line Movement": data["line_movement"]
    }

# --- Fetch SGP Builder with Correlation Score ---
def fetch_sgp_builder(game_selection, props, multi_game=False):
    """Generates an optimized SGP based on player props & correlation scores."""
    correlation_scores = {
        "Points & Assists": 0.85, 
        "Rebounds & Blocks": 0.78,
        "3PT & Points": 0.92
    }

    prop_text = f"SGP+ for multiple games" if multi_game else f"SGP for {game_selection}"
    return {
        "SGP": prop_text,
        "Correlation Scores": {p: correlation_scores.get(p, "No correlation data") for p in props}
    }

import requests
from nba_api.stats.endpoints import leaguedashteamstats
from utils import fetch_player_data  # Ensure fetch_player_data is implemented

def fetch_best_props(player_name, trend_length, min_odds=-450, max_odds=-200):
    """Fetches the best player props based on stats trends, defensive matchups, and risk levels."""
    
    # 🚀 Fetch player stats
    player_stats = fetch_player_data(player_name, trend_length)
    if isinstance(player_stats, dict) and "error" in player_stats:
        return {"error": "Player stats unavailable."}

    # 🚀 Fetch Defensive Matchup Data
    try:
        team_defense = leaguedashteamstats.LeagueDashTeamStats(season="2024-25").get_data_frames()[0]
        weakest_teams = {
            "points": team_defense.sort_values("OPP_PTS", ascending=False).head(3)["TEAM_NAME"].tolist(),
            "assists": team_defense.sort_values("OPP_AST", ascending=False).head(3)["TEAM_NAME"].tolist(),
            "rebounds": team_defense.sort_values("OPP_REB", ascending=False).head(3)["TEAM_NAME"].tolist(),
        }
    except Exception as e:
        return {"error": f"Failed to fetch defensive stats: {str(e)}"}

    # 🚀 Determine Best Prop Based on Player Trends
    best_prop = max(
        [("Points", player_stats["PTS"].mean()), 
         ("Assists", player_stats["AST"].mean()), 
         ("Rebounds", player_stats["REB"].mean())],
        key=lambda x: x[1]
    )

    # 🚀 Fetch Dynamic Odds Instead of Hardcoding
    odds_url = f"https://your_odds_api.com/api/props?player={player_name}"  # Replace with correct API
    try:
        odds_response = requests.get(odds_url)
        if odds_response.status_code == 200:
            odds_data = odds_response.json()
        else:
            odds_data = {"Points": -350, "Assists": -180, "Rebounds": +120}  # Default fallback values
    except Exception as e:
        odds_data = {"error": f"Failed to fetch odds: {str(e)}"}

    # 🚀 Define Risk Levels
    risk_levels = {
        "🔵 Very Safe": (-450, -300),
        "🟢 Safe": (-299, -200),
        "🟡 Moderate Risk": (-199, +100),
        "🟠 High Risk": (+101, +250),
        "🔴 Very High Risk": (+251, float("inf"))
    }

    # 🚀 Get Best Prop's Odds
    best_prop_name, best_stat = best_prop
    prop_odds = odds_data.get(best_prop_name, 0)

    # 🚀 Ensure Prop Falls Within Odds Range
    if not (min_odds <= prop_odds <= max_odds):
        return {"error": f"No props found within odds range {min_odds} to {max_odds}"}

    # 🚀 Determine Risk Label
    risk_label = next((label for label, (low, high) in risk_levels.items() if low <= prop_odds <= high), "Unknown Risk Level")

    return {
        "best_prop": best_prop_name,
        "average_stat": round(best_stat, 1),
        "odds": prop_odds,
        "risk_level": risk_label,
        "weak_defensive_teams": weakest_teams.get(best_prop_name.lower(), [])
    }

def fetch_game_predictions(game_selection):
    """Fetches AI-generated Moneyline, Spread, and Over/Under predictions for a selected game."""
    
    if not game_selection or "vs" not in game_selection:
        return {"error": "Invalid game selection. Please select a valid game."}

    home_team, away_team = game_selection.split(" vs ")

    # Example AI-generated predictions (Replace with real model later)
    predictions = {
        "Game": f"{home_team} vs {away_team}",
        "Moneyline": f"{home_team} to win (Win Probability: 55%)",
        "Spread": f"{home_team} -3.5 (-110)",
        "Over/Under": f"Over 225.5 (-108)",
        "Edge Detector": "🔥 AI Model suggests home team should be -5.0 favorites, creating a 1.5-point edge."
    }
    
    return predictions

def fetch_sharp_money_trends(game_selection):
    """Fetches betting line movement & sharp money trends from Sports Data API."""
    
    if not game_selection or "vs" not in game_selection:
        return {"error": "Invalid game selection. Please select a valid game."}

    url = f"https://sportsdata.io/api/betting-trends?game={game_selection}"
    
    response = requests.get(url, headers={"Authorization": f"Bearer {os.getenv('BETTING_API_KEY')}"})
    
    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.text}"}
    
    data = response.json()
    
    return {
        "Public Bets %": data.get("public_bets", "N/A"),
        "Sharp Money %": data.get("sharp_money", "N/A"),
        "Line Movement": data.get("line_movement", "N/A")
    }
def fetch_sgp_builder(game_selection, props, multi_game=False):
    """Generates an optimized Same Game Parlay (SGP) based on player props & correlation scores."""

    correlation_scores = {
        "Points & Assists": 0.85, 
        "Rebounds & Blocks": 0.78,
        "3PT & Points": 0.92
    }

    prop_text = f"SGP+ for multiple games" if multi_game else f"SGP for {game_selection}"

    return {
        "SGP": prop_text,
        "Correlation Scores": {p: correlation_scores.get(p, "No correlation data") for p in props}
    }

