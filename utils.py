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

    # Format date to match API requirements (e.g., YYYY-MM-DD)
    game_date = selected_game["date"].split("T")[0] if "date" in selected_game else datetime.today().strftime("%Y-%m-%d")

    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "player_points,player_rebounds,player_assists",  # Comma-separated, no spaces
            "date": game_date  # Add date filter to ensure relevance
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching player props: {response.status_code} - {response.text}")
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
    """Fetch enhanced game predictions using averaged odds and player stats."""
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h,spreads,totals"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching odds for predictions: {response.status_code}")
        return {}

    odds_data = response.json()
    predictions = {}
    all_teams = teams.get_teams()  # Fetch team data for ID mapping
    
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next(
            (e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']),
            None
        )
        if not event or not event.get("bookmakers"):
            predictions[game_key] = {"ML": "N/A", "Spread": "N/A", "O/U": "N/A", "confidence_score": 0}
            continue

        # Average odds across bookmakers
        h2h_odds = [m for b in event["bookmakers"] for m in b["markets"] if m["key"] == "h2h"]
        spread_odds = [m for b in event["bookmakers"] for m in b["markets"] if m["key"] == "spreads"]
        ou_odds = [m for b in event["bookmakers"] for m["markets"] if m["key"] == "totals"]

        if h2h_odds:
            home_odds = [o["price"] for m in h2h_odds for o in m["outcomes"] if o["name"] == game["home_team"]]
            away_odds = [o["price"] for m in h2h_odds for o in m["outcomes"] if o["name"] == game["away_team"]]
            avg_home_odds = sum(home_odds) / len(home_odds) if home_odds else 0
            avg_away_odds = sum(away_odds) / len(away_odds) if away_odds else 0
            home_prob = 1 / (1 + (avg_home_odds / 100 if avg_home_odds > 0 else 100 / abs(avg_home_odds))) if avg_home_odds else 0.5
            away_prob = 1 / (1 + (avg_away_odds / 100 if avg_away_odds > 0 else 100 / abs(avg_away_odds))) if avg_away_odds else 0.5
            ml = f"{game['home_team']} ({int(avg_home_odds)})" if home_prob > away_prob else f"{game['away_team']} ({int(avg_away_odds)})"
            ml_confidence = abs(home_prob - away_prob) * 100
        else:
            ml, ml_confidence = "N/A", 0

        if spread_odds:
            home_spreads = [(o["point"], o["price"]) for m in spread_odds for o in m["outcomes"] if o["name"] == game["home_team"]]
            avg_spread = sum(s[0] for s in home_spreads) / len(home_spreads) if home_spreads else 0
            avg_spread_odds = sum(s[1] for s in home_spreads) / len(home_spreads) if home_spreads else 0
            spread = f"{avg_spread:+.1f} ({int(avg_spread_odds)})"
        else:
            spread = "N/A"

        if ou_odds:
            totals = [(o["point"], o["price"]) for m in ou_odds for o in m["outcomes"] if o["name"] == "Over"]
            avg_total = sum(t[0] for t in totals) / len(totals) if totals else 0
            avg_ou_odds = sum(t[1] for t in totals) / len(totals) if totals else 0
            ou = f"{avg_total:.1f} ({int(avg_ou_odds)})"
        else:
            ou = "N/A"

        # Player Stats Adjustment using team IDs
        home_team = next((t for t in all_teams if t["full_name"] == game["home_team"]), None)
        away_team = next((t for t in all_teams if t["full_name"] == game["away_team"]), None)
        home_pts, away_pts = 0, 0
        
        if home_team and away_team:
            home_players = [p for p in players.get_active_players() if p.get("team_id") == home_team["id"]][:3]
            away_players = [p for p in players.get_active_players() if p.get("team_id") == away_team["id"]][:3]
            for p in home_players + away_players:
                stats = playergamelogs.PlayerGameLogs(player_id=p["id"], season_nullable="2024-25").get_data_frames()[0]
                avg_pts = stats["PTS"].head(5).mean() if not stats.empty else 0
                if p in home_players:
                    home_pts += avg_pts
                else:
                    away_pts += avg_pts
        
        pts_diff = (home_pts - away_pts) / (home_pts + away_pts) if (home_pts + away_pts) > 0 else 0
        confidence = min(max(ml_confidence + (pts_diff * 20), 50), 95)

        predictions[game_key] = {
            "ML": ml,
            "Spread": spread,
            "O/U": ou,
            "confidence_score": int(confidence)
        }
    
    return predictions
@st.cache_data(ttl=3600)
def fetch_sharp_money_trends(selected_games):
    """Fetch enhanced betting trends using odds movement and player stats."""
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h"
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

        # Analyze odds movement across all bookmakers
        h2h_markets = [b["markets"][0] for b in event["bookmakers"] if b["markets"] and b["markets"][0]["key"] == "h2h"]
        if not h2h_markets:
            trends[game_key] = "No moneyline data available."
            continue

        home_odds = [o["price"] for m in h2h_markets for o in m["outcomes"] if o["name"] == game["home_team"]]
        away_odds = [o["price"] for m in h2h_markets for o in m["outcomes"] if o["name"] == game["away_team"]]
        
        # Detect movement: Min vs Max odds
        min_home, max_home = min(home_odds), max(home_odds)
        min_away, max_away = min(away_odds), max(away_odds)
        home_shift = max_home - min_home
        away_shift = max_away - min_away

        # Player Stats for Context
        home_players = [p for p in players.get_active_players() if p["team"]["full_name"] == game["home_team"]][:3]
        away_players = [p for p in players.get_active_players() if p["team"]["full_name"] == game["away_team"]][:3]
        home_pts, away_pts = 0, 0
        for p in home_players + away_players:
            stats = playergamelogs.PlayerGameLogs(player_id=p["id"], season_nullable="2024-25").get_data_frames()[0]
            avg_pts = stats["PTS"].head(5).mean() if not stats.empty else 0
            if p in home_players:
                home_pts += avg_pts
            else:
                away_pts += avg_pts
        
        # Determine trend with stats correlation
        if home_shift > 10 and home_pts > away_pts:
            trend = f"Sharp money on {game['home_team']} (+{home_shift} shift, supported by {home_pts:.1f} vs {away_pts:.1f} PPG)"
        elif away_shift > 10 and away_pts > home_pts:
            trend = f"Sharp money on {game['away_team']} (+{away_shift} shift, supported by {away_pts:.1f} vs {home_pts:.1f} PPG)"
        elif home_shift > away_shift:
            trend = f"Minor movement toward {game['home_team']} (+{home_shift} shift)"
        elif away_shift > home_shift:
            trend = f"Minor movement toward {game['away_team']} (+{away_shift} shift)"
        else:
            trend = "No significant sharp money movement detected."
        
        trends[game_key] = trend
    
    return trends

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, sgp_props, multi_game=False):
    """Generate a Same Game Parlay using live props data."""
    if multi_game:
        total_props = []
        for game in selected_game:
            props = fetch_best_props(game)[:sgp_props]
            total_props.extend(props)
    else:
        total_props = fetch_best_props(selected_game)[:sgp_props] if isinstance(sgp_props, int) else sgp_props

    if not total_props or isinstance(total_props[0], str):
        return "No valid props available for SGP."

    combined_odds = 1.0
    for prop in total_props:
        odds = prop["odds"]
        decimal_odds = (odds / 100 + 1) if odds > 0 else (1 + 100 / abs(odds))
        combined_odds *= decimal_odds

    american_odds = int((combined_odds - 1) * 100) if combined_odds > 2 else int(-100 / (combined_odds - 1))
    game_label = f"{selected_game['home_team']} vs {selected_game['away_team']}" if not multi_game else "Multiple Games"
    prop_details = "\n".join([f"{p['player']} - {p['prop']} ({p['line']}): {p['odds']}" for p in total_props])
    return f"SGP for {game_label}:\n{prop_details}\nCombined Odds: {american_odds:+d}"

@st.cache_data(ttl=3600)
def fetch_player_data(player_name, selected_team=None):
    """Fetch player stats and H2H stats from NBA API."""
    matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
    
    if not matching_players:
        return None, None

    player_id = matching_players[0]["id"]
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2024-25").get_data_frames()[0]

    last_5 = game_logs.head(5).to_dict(orient="records")
    last_10 = game_logs.head(10).to_dict(orient="records")
    last_15 = game_logs.head(15).to_dict(orient="records")

    player_stats = {
        "Career Stats": career_stats.to_dict(orient="records"),
        "Last 5 Games": last_5,
        "Last 10 Games": last_10,
        "Last 15 Games": last_15
    }
    
    h2h_stats = None
    if selected_team:
        team_abbr = next((t['abbreviation'] for t in teams.get_teams() if t['full_name'] == selected_team), None)
        if team_abbr:
            h2h_games = game_logs[game_logs['MATCHUP'].str.contains(team_abbr)]
            h2h_stats = h2h_games.to_dict(orient="records") if not h2h_games.empty else None

    return player_stats, h2h_stats

@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch all active NBA players."""
    return [p["full_name"] for p in players.get_active_players()]
