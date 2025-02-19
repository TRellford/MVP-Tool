import requests
import pandas as pd

# Fetch Available Games
def fetch_games():
    response = requests.get("https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-FEB-19")
    games = response.json()
    return [f"{game['AwayTeam']} vs {game['HomeTeam']}" for game in games]

# Fetch Player Props
def fetch_props(games, prop_count, risk_level, sgp, sgp_plus):
    # Simulated API response
    props = [{"Player": "LeBron James", "Prop": "Over 7.5 Assists", "Odds": "-250", "Confidence": "90%"}]
    return pd.DataFrame(props)

# Fetch ML, Spread, O/U Predictions
def fetch_ml_spread_ou(games):
    ml_data = [{"Game": "Lakers vs Nuggets", "ML Prediction": "Lakers", "Confidence": "88%"}]
    return pd.DataFrame(ml_data)

# Fetch Player Data
def fetch_player_data(player_name):
    player_data = [{"Category": "Points", "Prediction": "Over 24.5", "Confidence": "85%"}]
    return pd.DataFrame(player_data)
