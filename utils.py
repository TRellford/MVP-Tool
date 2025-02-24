import requests
import streamlit as st
from nba_api.stats.endpoints import playergamelogs, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
from balldontlie import BalldontlieAPI

NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
BALL_DONT_LIE_API_URL = "https://api.balldontlie.io/v1"

def get_nba_games(date):
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
    """Fetch FanDuel player props for a specific game using the event odds endpoint."""
    if not selected_game.get("game_id"):
        st.error("🚨 Invalid game selected. No game ID found.")
        return []
    
    game_date = selected_game["date"].split("T")[0] if "date" in selected_game else datetime.today().strftime("%Y-%m-%d")
    home_team = selected_game["home_team"]
    away_team = selected_game["away_team"]

    # Step 1: Find the event ID
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h",
            "date": game_date,
            "bookmakers": "fanduel"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching events: {response.status_code} - {response.text}")
        return []
    
    events_data = response.json()
    event = next(
        (e for e in events_data if e['home_team'] == home_team and e['away_team'] == away_team),
        None
    )
    if not event:
        st.error(f"🚨 No matching event found for {home_team} vs {away_team} on {game_date}.")
        return []
    
    event_id = event["id"]

    # Step 2: Fetch player props with a single market to test
    event_url = f"{NBA_ODDS_API_URL.rsplit('/', 1)[0]}/events/{event_id}/odds"
    markets_to_try = ["player_points"]  # Start with one market
    best_props = []

    response = requests.get(
        event_url,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "player_points",  # Single market to test
            "bookmakers": "fanduel"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching FanDuel player props: {response.status_code} - {response.text}")
        # Debug: Fetch available markets with a featured market
        debug_response = requests.get(
            event_url,
            params={
                "apiKey": st.secrets["odds_api_key"],
                "regions": "us",
                "markets": "h2h",
                "bookmakers": "fanduel"
            }
        )
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            st.write("Available markets for this event:", debug_data.get("bookmakers", [{}])[0].get("markets", []))
        return []
    
    props_data = response.json()
    if not props_data.get("bookmakers"):
        return ["No FanDuel props found for this game."]
    
    fanduel = next((b for b in props_data["bookmakers"] if b["key"] == "fanduel"), None)
    if not fanduel:
        return ["FanDuel odds not available for this game."]
    
    for market in fanduel.get("markets", []):
        for outcome in market.get("outcomes", []):
            price = outcome.get("price", 0)
            if min_odds <= price <= max_odds:
                prop_name = market["key"].replace("player_", "").replace("_", " ").title()
                best_props.append({
                    "player": outcome["name"],
                    "prop": prop_name,
                    "line": outcome.get("point", "N/A"),
                    "odds": price,
                    "insight": f"{outcome['name']} prop from FanDuel"
                })
    
    # If successful, try additional markets one by one (optional)
    additional_markets = ["player_rebounds", "player_assists", "player_threes"]
    for market in additional_markets:
        response = requests.get(
            event_url,
            params={
                "apiKey": st.secrets["odds_api_key"],
                "regions": "us",
                "markets": market,
                "bookmakers": "fanduel"
            }
        )
        if response.status_code == 200:
            props_data = response.json()
            fanduel = next((b for b in props_data["bookmakers"] if b["key"] == "fanduel"), None)
            if fanduel:
                for market_data in fanduel.get("markets", []):
                    for outcome in market_data.get("outcomes", []):
                        price = outcome.get("price", 0)
                        if min_odds <= price <= max_odds:
                            prop_name = market_data["key"].replace("player_", "").replace("_", " ").title()
                            best_props.append({
                                "player": outcome["name"],
                                "prop": prop_name,
                                "line": outcome.get("point", "N/A"),
                                "odds": price,
                                "insight": f"{outcome['name']} prop from FanDuel"
                            })
    
    return best_props if best_props else ["No suitable FanDuel props found."]
@st.cache_data(ttl=3600)
def fetch_game_predictions(selected_games):
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "bookmakers": "fanduel"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching odds for predictions: {response.status_code}")
        return {}
    odds_data = response.json()
    predictions = {}
    all_teams = teams.get_teams()
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next(
            (e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']),
            None
        )
        if not event or not event.get("bookmakers"):
            predictions[game_key] = {"ML": "N/A", "Spread": "N/A", "O/U": "N/A", "confidence_score": 0}
            continue
        fanduel = next((b for b in event["bookmakers"] if b["key"] == "fanduel"), None)
        if not fanduel:
            predictions[game_key] = {"ML": "N/A", "Spread": "N/A", "O/U": "N/A", "confidence_score": 0}
            continue
        h2h_odds = next((m for m in fanduel["markets"] if m["key"] == "h2h"), None)
        spread_odds = next((m for m in fanduel["markets"] if m["key"] == "spreads"), None)
        ou_odds = next((m for m in fanduel["markets"] if m["key"] == "totals"), None)
        if h2h_odds:
            home_odds = next(o["price"] for o in h2h_odds["outcomes"] if o["name"] == game["home_team"])
            away_odds = next(o["price"] for o in h2h_odds["outcomes"] if o["name"] == game["away_team"])
            home_prob = 1 / (1 + (home_odds / 100 if home_odds > 0 else 100 / abs(home_odds)))
            away_prob = 1 / (1 + (away_odds / 100 if away_odds > 0 else 100 / abs(away_odds)))
            ml = f"{game['home_team']} ({home_odds})" if home_prob > away_prob else f"{game['away_team']} ({away_odds})"
            ml_confidence = abs(home_prob - away_prob) * 100
        else:
            ml, ml_confidence = "N/A", 0
        spread = f"{spread_odds['outcomes'][0]['point']:+.1f} ({spread_odds['outcomes'][0]['price']})" if spread_odds else "N/A"
        ou = f"{ou_odds['outcomes'][0]['point']:.1f} ({ou_odds['outcomes'][0]['price']})" if ou_odds else "N/A"
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
    response = requests.get(
        NBA_ODDS_API_URL,
        params={
            "apiKey": st.secrets["odds_api_key"],
            "regions": "us",
            "markets": "h2h",
            "bookmakers": "fanduel"
        }
    )
    if response.status_code != 200:
        st.error(f"❌ Error fetching odds for trends: {response.status_code}")
        return {}
    odds_data = response.json()
    trends = {}
    all_teams = teams.get_teams()
    for game in selected_games:
        game_key = f"{game['home_team']} vs {game['away_team']}"
        event = next(
            (e for e in odds_data if e['home_team'] == game['home_team'] and e['away_team'] == game['away_team']),
            None
        )
        if not event or not event.get("bookmakers"):
            trends[game_key] = "No line movement data available."
            continue
        fanduel = next((b for b in event["bookmakers"] if b["key"] == "fanduel"), None)
        if not fanduel or not fanduel["markets"]:
            trends[game_key] = "No FanDuel moneyline data available."
            continue
        h2h_market = fanduel["markets"][0]
        home_odds = next(o["price"] for o in h2h_market["outcomes"] if o["name"] == game["home_team"])
        away_odds = next(o["price"] for o in h2h_market["outcomes"] if o["name"] == game["away_team"])
        # Simplified trend: High odds shift indicates sharp money (no historical data available)
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
        if home_odds < away_odds and home_pts > away_pts:
            trend = f"Sharp money on {game['home_team']} ({home_odds}, {home_pts:.1f} vs {away_pts:.1f} PPG)"
        elif away_odds < home_odds and away_pts > home_pts:
            trend = f"Sharp money on {game['away_team']} ({away_odds}, {away_pts:.1f} vs {home_pts:.1f} PPG)"
        else:
            trend = "No significant sharp money movement detected."
        trends[game_key] = trend
    return trends

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, sgp_props, multi_game=False):
    if multi_game:
        total_props = []
        for game in selected_game:
            props = fetch_best_props(game)[:sgp_props]
            total_props.extend(props)
    else:
        total_props = fetch_best_props(selected_game)[:sgp_props] if isinstance(sgp_props, int) else sgp_props
    if not total_props or isinstance(total_props[0], str):
        return "No valid FanDuel props available for SGP."
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
    return [p["full_name"] for p in players.get_active_players()]
