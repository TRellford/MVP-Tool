import requests
import streamlit as st
from nba_api.stats.endpoints import playergamelogs, playercareerstats
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import pandas as pd
from balldontlie import BalldontlieAPI

# API Base URLs
NBA_ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
BALL_DONT_LIE_API_URL = "https://api.balldontlie.io/v1"

class SGPAnalyzer:
    def __init__(self):
        self.all_players = players.get_players()
        self.all_teams = teams.get_teams()

    def get_player_stats(self, player_id, stat_key, games=5):
        """Fetch recent player stats for a specific stat."""
        try:
            game_logs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2024-25").get_data_frames()[0]
            if not game_logs.empty:
                return game_logs[stat_key].head(games).mean()
            return 0
        except Exception as e:
            st.warning(f"⚠️ Error fetching stats for player {player_id}: {e}")
            return 0

    def get_team_defense_stats(self, team_name, stat_category, games=5):
        """Fetch opponent defense stats for a given team and stat category."""
        team = next((t for t in self.all_teams if t["full_name"] == team_name), None)
        if not team:
            return 0
        opposing_players = [p for p in self.all_players if p.get("team_id") != team["id"]]
        opp_stats = []
        for player in opposing_players[:10]:  # Top 10 opposing players for efficiency
            stats = self.get_player_stats(player["id"], stat_category, games)
            opp_stats.append(stats)
        return np.mean(opp_stats) if opp_stats else 0

    def calculate_bayesian_confidence(self, recent_avg, prop_line, hit_rate=0.6):
        """Bayesian inference for dynamic prop adjustments."""
        alpha = hit_rate * 10  # Prior based on 60% hit rate over 10 games
        beta = (1 - hit_rate) * 10
        samples = stats.beta.rvs(alpha, beta, size=10000)
        prop_hit_prob = np.mean(samples > (prop_line - recent_avg) / prop_line if prop_line > 0 else 0.5)
        return min(max(prop_hit_prob * 100, 0), 100)

    def calculate_xgboost_confidence(self, recent_avg, prop_line, opponent_defense):
        """XGBoost-based prop prediction (simplified with linear scaling)."""
        # Simplified: Higher avg vs. line and lower opponent defense = higher confidence
        weight_avg = (recent_avg - prop_line) / prop_line if prop_line > 0 else 0
        weight_def = (opponent_defense - recent_avg) / opponent_defense if opponent_defense > 0 else 0
        confidence = min(max((weight_avg - weight_def) * 50 + 50, 0), 100)
        return confidence

    def monte_carlo_simulation(self, recent_avg, prop_line, std_dev=2.5, simulations=10000):
        """Monte Carlo simulation for prop hit likelihood."""
        samples = np.random.normal(recent_avg, std_dev, simulations)
        hit_rate = np.mean(samples > prop_line) * 100 if prop_line > 0 else 50
        return min(max(hit_rate, 0), 100)

    def poisson_distribution(self, recent_avg, prop_line):
        """Poisson distribution for scoring-based props (points)."""
        if recent_avg <= 0:
            return 50
        lambda_param = recent_avg
        prob_exceed = 1 - stats.poisson.cdf(prop_line - 1, lambda_param)
        return min(max(prob_exceed * 100, 0), 100)

    def linear_regression_adjustment(self, recent_avg, pace_factor=1.0, blowout_risk=0.1):
        """Adjust props for game script (pace, blowout risk)."""
        adjusted_avg = recent_avg * pace_factor * (1 - blowout_risk)
        return min(max(adjusted_avg / recent_avg * 100, 50), 100)  # Confidence as a percentage

    def line_discrepancy_detector(self, prop_odds, ai_predicted_prob):
        """Detect mispriced bets by comparing AI odds to sportsbook odds."""
        implied_prob = 1 / (1 + (prop_odds / 100 if prop_odds > 0 else 100 / abs(prop_odds)))
        edge = (ai_predicted_prob / 100 - implied_prob) / implied_prob if implied_prob > 0 else 0
        return min(max(edge * 50 + 50, 0), 100)  # Confidence boost if edge exists

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
def fetch_best_props(selected_game, min_odds=-450, max_odds=float('inf')):
    """Fetch and recommend FanDuel player props with AI-driven analysis."""
    if not selected_game.get("game_id"):
        st.error("🚨 Invalid game selected. No game ID found.")
        return []
    
    game_date = selected_game["date"].split("T")[0] if "date" in selected_game else datetime.today().strftime("%Y-%m-%d")
    home_team = selected_game["home_team"]
    away_team = selected_game["away_team"]

    # Step 1: Find event ID
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
    event_url = f"{NBA_ODDS_API_URL.rsplit('/', 1)[0]}/events/{event_id}/odds"
    
    # Initialize analyzer
    analyzer = SGPAnalyzer()
    markets = ["player_points", "player_rebounds", "player_assists", "player_threes"]
    best_props = []
    
    for market in markets:
        response = requests.get(
            event_url,
            params={
                "apiKey": st.secrets["odds_api_key"],
                "regions": "us",
                "markets": market,
                "bookmakers": "fanduel"
            }
        )
        if response.status_code != 200:
            st.warning(f"⚠️ Skipping {market}: {response.status_code} - {response.text}")
            continue
        
        props_data = response.json()
        fanduel = next((b for b in props_data.get("bookmakers", []) if b["key"] == "fanduel"), None)
        if not fanduel:
            continue
        
        for m in fanduel.get("markets", []):
            for outcome in m.get("outcomes", []):
                price = outcome.get("price", 0)
                if min_odds <= price <= max_odds:
                    player_name = outcome["name"]
                    prop_line = float(outcome.get("point", 0)) if outcome.get("point") != "N/A" else 0
                    
                    # Find player and team data
                    player = next((p for p in analyzer.all_players if p["full_name"] == player_name), None)
                    if not player:
                        continue
                    team = next((t for t in analyzer.all_teams if t["id"] == player.get("team_id")), None)
                    opponent = next((t for t in analyzer.all_teams if t["full_name"] in (home_team, away_team) and t["id"] != team["id"]), None)
                    
                    if not team or not opponent:
                        continue
                    
                    # Step 1: Filter players with strong trends (60%+ hit rate)
                    stats = playergamelogs.PlayerGameLogs(player_id=player["id"], season_nullable="2024-25").get_data_frames()[0]
                    if not stats.empty:
                        stat_key = {"player_points": "PTS", "player_rebounds": "REB", "player_assists": "AST", "player_threes": "FG3M"}[market]
                        recent_games = stats.head(10)  # Last 10 games for trend analysis
                        hit_rate = (recent_games[stat_key] > prop_line).mean() if prop_line > 0 else 0.5
                        if hit_rate < 0.6:
                            continue
                    
                    # Step 2: Matchup analysis (opponent defensive stats)
                    opponent_defense = analyzer.get_team_defense_stats(opponent["full_name"], stat_key)
                    
                    # Step 3: Confidence score calculation using multiple models
                    recent_avg = analyzer.get_player_stats(player["id"], stat_key, 5)
                    bayesian_conf = analyzer.calculate_bayesian_confidence(recent_avg, prop_line, hit_rate)
                    xgboost_conf = analyzer.calculate_xgboost_confidence(recent_avg, prop_line, opponent_defense)
                    monte_carlo_conf = analyzer.monte_carlo_simulation(recent_avg, prop_line)
                    poisson_conf = analyzer.poisson_distribution(recent_avg, prop_line) if market == "player_points" else 50
                    linear_conf = analyzer.linear_regression_adjustment(recent_avg, pace_factor=1.0, blowout_risk=0.1)
                    
                    # Aggregate confidence (average weighted models)
                    confidence = np.mean([bayesian_conf, xgboost_conf, monte_carlo_conf, poisson_conf, linear_conf])
                    confidence = min(max(confidence, 0), 100)
                    
                    # Step 4: AI-based correlation analysis
                    correlation_insight = ""
                    if market in ["player_points", "player_assists"]:
                        assist_stats = stats["AST"].head(5).mean() if stat_key == "PTS" else stats["PTS"].head(5).mean()
                        if recent_avg > prop_line and assist_stats > (prop_line * 0.8):
                            correlation_insight = "Strong synergy with assists"
                    
                    # Step 5: Betting market trends (simplified via odds movement)
                    sharp_confidence_boost = 0
                    if price > 100 or price < -200:  # High odds shifts often indicate sharp money
                        sharp_confidence_boost = 10
                    confidence = min(confidence + sharp_confidence_boost, 100)
                    
                    # Step 6: Alternative line adjustments
                    alt_lines = []
                    if recent_avg > prop_line:
                        safer_line = prop_line * 0.8  # e.g., Over 20.5 instead of 25.5
                        riskier_line = prop_line * 1.2  # e.g., Over 30.0 instead of 25.5
                        alt_lines = [
                            {"line": safer_line, "odds": price - 50, "confidence": confidence + 10},  # Safer, lower odds
                            {"line": riskier_line, "odds": price + 50, "confidence": confidence - 10}  # Riskier, higher odds
                        ]
                    
                    # Step 7: Assign risk level and color
                    risk_level, color = self._get_risk_level(price)
                    
                    prop_name = market.replace("player_", "").replace("_", " ").title()
                    best_props.append({
                        "player": player_name,
                        "prop": prop_name,
                        "line": prop_line,
                        "odds": price,
                        "confidence": confidence,
                        "insight": f"{player_name} averages {recent_avg:.1f} {prop_name} vs. {prop_line} - {correlation_insight} - Opponent allows {opponent_defense:.1f} {stat_key}",
                        "risk_level": risk_level,
                        "color": color,
                        "alt_lines": alt_lines
                    })
    
    return best_props if best_props else ["No suitable FanDuel props found."]

def _get_risk_level(self, odds):
    """Assign risk level and color based on odds."""
    if -450 <= odds <= -300:
        return "Very Safe", "blue"
    elif -299 <= odds <= -200:
        return "Safe", "green"
    elif -199 <= odds <= 100:
        return "Moderate Risk", "yellow"
    elif 101 <= odds <= 250:
        return "High Risk", "orange"
    else:  # odds > 250
        return "Very High Risk", "red"

@st.cache_data(ttl=3600)
def fetch_sgp_builder(selected_game, num_props=1, min_odds=-450, max_odds=float('inf'), multi_game=False):
    """Generate SGP or SGP+ prediction by selecting top props based on confidence and risk."""
    if multi_game:
        if not isinstance(selected_game, list):
            return "Invalid multi-game selection."
        all_props = []
        for game in selected_game:
            game_props = fetch_best_props(game, min_odds, max_odds)
            if not isinstance(game_props[0], str):
                all_props.extend(game_props)
    else:
        all_props = fetch_best_props(selected_game, min_odds, max_odds)
        if isinstance(all_props[0], str):
            return f"No valid FanDuel props available for SGP on {selected_game['home_team']} vs {selected_game['away_team']}."
    
    if not all_props or isinstance(all_props[0], str):
        return "No valid FanDuel props available for SGP."
    
    # Filter and sort by confidence and risk
    filtered_props = [p for p in all_props if min_odds <= p["odds"] <= max_odds]
    if not filtered_props:
        return f"No props available within risk range ({min_odds} to {max_odds})."
    
    # Sort by confidence (descending for safer bets, ascending for riskier within range)
    risk_order = "desc" if min_odds < 0 else "asc"
    sorted_props = sorted(filtered_props, key=lambda x: x["confidence"], reverse=(risk_order == "desc"))
    
    # Select top N props based on number requested, ensuring diversity
    selected_props = []
    prop_types = set()
    for prop in sorted_props:
        if len(selected_props) >= num_props:
            break
        prop_type = prop["prop"]
        if prop_type not in prop_types or len(selected_props) < num_props // 2:  # Allow some overlap but prioritize diversity
            selected_props.append(prop)
            prop_types.add(prop_type)
    
    if len(selected_props) < num_props:
        return f"Only {len(selected_props)} props available (requested {num_props})."
    
    # Calculate combined odds and confidence
    combined_odds = 1.0
    avg_confidence = sum(p["confidence"] for p in selected_props) / len(selected_props)
    
    for prop in selected_props:
        odds = prop["odds"]
        decimal_odds = (odds / 100 + 1) if odds > 0 else (1 + 100 / abs(odds))
        combined_odds *= decimal_odds
    
    american_odds = int((combined_odds - 1) * 100) if combined_odds > 2 else int(-100 / (combined_odds - 1))
    game_label = "Multiple Games" if multi_game else f"{selected_game['home_team']} vs {selected_game['away_team']}"
    prop_details = "\n".join([
        f"{p['player']} - {p['prop']} ({p['line']}): {p['odds']} ({p['confidence']:.0f}%) "
        f"- {p['insight']} :large_{p['color']}_circle: {p['risk_level']}"
        for p in selected_props
    ])
    
    # Alternative lines suggestion
    alt_lines = []
    for prop in selected_props:
        if prop["alt_lines"]:
            alt_lines.extend([
                f"Alt for {prop['player']} - {prop['prop']}: {alt['line']:.1f} @ {alt['odds']} ({alt['confidence']:.0f}%)"
                for alt in prop["alt_lines"]
            ])
    
    prediction = "Likely to hit" if avg_confidence > 70 else "Moderate chance" if avg_confidence > 50 else "Risky bet"
    result = f"SGP for {game_label}:\n{prop_details}\nCombined Odds: {american_odds:+d}\nPrediction: {prediction} ({avg_confidence:.0f}% confidence)"
    if alt_lines:
        result += f"\nAlternative Lines Suggestions:\n" + "\n".join(alt_lines)
    
    return result

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

# Nickname to full name mapping
nickname_mapping = {
    "Steph Curry": "Stephen Curry",
    "Bron": "LeBron James",
    "KD": "Kevin Durant",
    "AD": "Anthony Davis",
    "CP3": "Chris Paul",
    "Joker": "Nikola Jokic",
    "The Beard": "James Harden",
    "Dame": "Damian Lillard",
    "Klay": "Klay Thompson",
    "Tatum": "Jayson Tatum",
    "Giannis": "Giannis Antetokounmpo"
}

@st.cache_data(ttl=3600)
def fetch_player_data(player_name):
    """Fetch player stats from NBA API with proper game log retrieval, supporting nicknames."""
    try:
        # Convert nickname to full name if applicable
        player_name = nickname_mapping.get(player_name, player_name)

        # Find matching player
        matching_players = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
        
        if not matching_players:
            return {"Error": f"Player '{player_name}' not found."}

        player_id = matching_players[0]["id"]

        # Fetch career stats
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]

        # Fetch game logs for the 2024-25 season using the correct parameter
        try:
            game_logs = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable="2024-25").get_data_frames()[0]
        except Exception as e:
            return {
                "Career Stats": career_stats.to_dict(orient="records"),
                "Last 5 Games": [],
                "Last 10 Games": [],
                "Error": f"Failed to retrieve game logs: {str(e)}"
            }

        # Ensure game logs exist
        if game_logs.empty:
            return {
                "Career Stats": career_stats.to_dict(orient="records"),
                "Last 5 Games": [],
                "Last 10 Games": [],
                "Error": "No recent game data available for the 2024-25 season."
            }

        # Select key stats for display (remove "MIN")
        stat_columns = ["GAME_DATE", "PTS", "REB", "AST", "FG_PCT", "FG3M"]

        # Convert game logs to only relevant columns
        game_logs_filtered = game_logs[stat_columns]

        # Convert date column to a readable format
        game_logs_filtered["GAME_DATE"] = pd.to_datetime(game_logs_filtered["GAME_DATE"]).dt.strftime('%Y-%m-%d')

        # Convert FG% from decimal to percentage format
        game_logs_filtered["FG_PCT"] = (game_logs_filtered["FG_PCT"] * 100).round(2).astype(str) + "%"

        # Structure output data
        return {
            "Career Stats": career_stats.to_dict(orient="records"),
            "Last 5 Games": game_logs_filtered.head(5).to_dict(orient="records"),
            "Last 10 Games": game_logs_filtered.head(10).to_dict(orient="records"),
        }
    
    except Exception as e:
        return {"Error": str(e)}

@st.cache_data(ttl=3600)
def fetch_all_players():
    """Fetch player names from NBA API & Balldontlie API if missing."""
    
    # 🏀 1️⃣ Get players from NBA API
    nba_player_list = players.get_players()
    nba_players = {p["full_name"].lower(): p["id"] for p in nba_player_list}

    return nba_players  # If NBA API returns the player, no need to check Balldontlie

def fetch_player_id(player_name):
    """Fetch player ID from NBA API, then Balldontlie API if missing."""
    player_name = player_name.lower()
    player_dict = fetch_all_players()
    
    # ✅ 1️⃣ Check NBA API First
    if player_name in player_dict:
        return player_dict[player_name]  # Return NBA API player ID

    # ❌ 2️⃣ If Not Found, Check Balldontlie API
    response = requests.get(BALLEDONTLIE_URL + player_name)

    if response.status_code == 200:
        data = response.json()
        if data["data"]:  # If player is found
            return data["data"][0]["id"]  # Return Balldontlie ID

    return None  # ❌ Player Not Found in Either API
