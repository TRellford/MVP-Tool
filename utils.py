import requests
import streamlit as st
from nba_api.stats.endpoints import playergamelogs, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
from balldontlie import BalldontlieAPI  # Kept for potential future use

# API Base URLs
NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
BALL_DONT_LIE_API_URL = "https://api.balldontlie.io/v1"

def get_nba_games(date):
    """Fetch NBA games from BallDontLie API for a specific date."""
    if isinstance(date, str):
        date_str = date
    else:
        date_str = date.strftime("%Y-%m-%d")

    try:
        url = f"{BALL_DONT_LIE_API_URL}/games"
        headers = {"Authorization": st.secrets["balldontlie_api_key"]}
        params = {"dates[]": date_str}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401:
            st.error("❌ Unauthorized (401). Check your API key in secrets.toml.")
            return []
        if response.status_code != 200:
            st.error(f"❌ Error fetching games: {response.status_code}")
            return []

        games_data = response.json().get("data", [])
        formatted_games = [
            {
                "home_team": game["home_team"]["full_name"],
                "away_team": game["visitor_team"]["full_name"],
                "game_id": game["id"],
                "date": game["date"]
            }
            for game in games_data
        ]
        return formatted_games

    except Exception as e:
        st.error(f"❌ Unexpected error fetching games: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_best_props(selected_game, min_odds=-250, max_odds=100):
    """Fetch best player props for a selected game within a given odds range."""
    if not selected_game.get("game_id"):
        st.error("🚨 Invalid game selected. No game ID found.")
        return []

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "player_points,player_rebounds,player_assists"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching player props: {response.status_code}")
        return []

    props_data = response.json()
    best_props = []
    event = next(
        (e for e in props_data if e['home_team'] == selected_game['home_team'] and e['away_team'] == selected_game['away_team']),
        None
    )
    if not event:
        return ["No props found for the selected game."]

    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                price = outcome.get("price", 0)
                if min_odds <= price <= max_odds:
                    best_props.append({
                        "player": outcome["name"],
                        "prop": market["key"].replace("_", " ").title(),
                        "line": outcome.get("point", "N/A"),
                        "odds": price,
                        "insight": f"{outcome['name']} has strong recent performances in this prop category."
                    })

    return best_props if best_props else ["No suitable props found."]

@st.cache_data(ttl=3600)
def fetch_game_predictions(selected_games):
    """Fetch live game predictions based on odds from The Odds API."""
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h,spreads,totals"  # Moneyline, Spread, Over/Under
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching odds for predictions: {response.status_code}")
        return {}

    odds_data = response.json()
    predictions = {}
    
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next(
            (e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']),
            None
        )
        if not event:
            predictions[game_key] = {"ML": "N/A", "Spread": "N/A", "O/U": "N/A", "confidence_score": 0}
            continue

        # Extract odds from the first bookmaker (e.g., average or best odds could be implemented)
        bookmaker = event.get("bookmakers", [])[0] if event.get("bookmakers") else None
        if not bookmaker:
            predictions[game_key] = {"ML": "N/A", "Spread": "N/A", "O/U": "N/A", "confidence_score": 0}
            continue

        ml_odds = next((m for m in bookmaker["markets"] if m["key"] == "h2h"), None)
        spread_odds = next((m for m in bookmaker["markets"] if m["key"] == "spreads"), None)
        ou_odds = next((m for m in bookmaker["markets"] if m["key"] == "totals"), None)

        # Moneyline Prediction
        ml = f"{ml_odds['outcomes'][0]['name']} ({ml_odds['outcomes'][0]['price']})" if ml_odds else "N/A"
        # Spread Prediction
        spread = f"{spread_odds['outcomes'][0]['point']} ({spread_odds['outcomes'][0]['price']})" if spread_odds else "N/A"
        # Over/Under Prediction
        ou = f"{ou_odds['outcomes'][0]['point']} ({ou_odds['outcomes'][0]['price']})" if ou_odds else "N/A"
        # Confidence Score (simplified: based on odds favorability)
        confidence = min(max(abs(ml_odds['outcomes'][0]['price']) / 100 if ml_odds else 50, 50), 90)

        predictions[game_key] = {
            "ML": ml,
            "Spread": spread,
            "O/U": ou,
            "confidence_score": confidence
        }
    
    return predictions

@st.cache_data(ttl=3600)
def fetch_sharp_money_trends(selected_games):
    """Fetch betting trends based on line movement from The Odds API."""
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h,spreads,totals"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching odds for trends: {response.status_code}")
        return {}

    odds_data = response.json()
    trends = {}
    
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next(
            (e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']),
            None
        )
        if not event or not event.get("bookmakers"):
            trends[game_key] = "No line movement data available."
            continue

        # Analyze line movement across bookmakers
        h2h_markets = [b["markets"][0] for b in event["bookmakers"] if b["markets"] and b["markets"][0]["key"] == "h2h"]
        if not h2h_markets:
            trends[game_key] = "No moneyline data available."
            continue

        opening_odds = h2h_markets[0]["outcomes"][0]["price"]  # First bookmaker’s opening odds
        current_odds = max(m["outcomes"][0]["price"] for m in h2h_markets)  # Highest current odds
        movement = current_odds - opening_odds

        if movement > 0:
            trend = f"Sharp money moving toward {h2h_markets[0]['outcomes'][0]['name']} (+{movement} shift)"
        elif movement < 0:
            trend = f"Sharp money moving toward {h2h_markets[0]['outcomes'][1]['name']} ({movement} shift)"
        else:
            trend = "No significant line movement detected."
        
        trends[game_key] = trend
    
    return trends

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, sgp_props, multi_game=False):
    """Generate a Same Game Parlay using live props data."""
    if multi_game:
        # For multi-game, sgp_props is an integer (props per game)
        total_props = []
        for game in selected_game:  # selected_game is a list in multi-game mode
            props = fetch_best_props(game)[:sgp_props]  # Limit to props_per_game
            total_props.extend(props)
    else:
        # Single-game mode
        total_props = fetch_best_props(selected_game)[:sgp_props] if isinstance(sgp_props, int) else sgp_props

    if not total_props or isinstance(total_props[0], str):  # Check if props fetch failed
        return "No valid props available for SGP."

    # Calculate combined odds (simplified: multiply decimal odds)
    combined_odds = 1.0
    for prop in total_props:
        odds = prop["odds"]
        decimal_odds = (odds / 100 + 1) if odds > 0 else (1 + 100 / abs(odds))
        combined_odds *= decimal_odds

    # Convert back to American odds
    american_odds = int((combined_odds - 1) * 100) if combined_odds > 2 else int(-100 / (combined_odds - 1))

    game_label = f"{selected_game['home_team']} vs {selected_game['away_team']}" if not multi_game else "Multiple Games"
    prop_details = "\n".join([f"{p['player']} - {p['prop']} ({p['line']}): {p['odds']}" for p in total_props])
    return f"SGP for {game_label}:\n{prop_details}\nCombined Odds: {american_odds:+d}"

@st.cache_data(ttl=3600)
def fetch_player_data(player_name, selected_team=None):
