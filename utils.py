from nba_api.stats.endpoints import scoreboardv2, playergamelogs, commonplayerinfo
import requests

# **Fetch Game List with Proper Team Names**
def fetch_games():
    games = scoreboardv2.ScoreboardV2().get_dict()["resultSets"][0]["rowSet"]
    
    game_list = []
    for game in games:
        home_team = game[5]  # Home team abbreviation
        away_team = game[6]  # Away team abbreviation
        game_list.append(f"{away_team} vs {home_team}")

    return game_list

# **Fetch Player Props**
def fetch_props(game, num_props, risk_level):
    url = f"https://api.sportsbook.com/props?game={game}&num_props={num_props}&risk={risk_level}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return [{"Player": "N/A", "Prop": "N/A", "Odds": "N/A", "Confidence": "N/A"}]

# **Fetch ML, Spread, O/U Predictions**
def fetch_ml_spread_ou(selected_games):
    results = []
    for game in selected_games:
        url = f"https://api.sportsbook.com/ml_spread_ou?game={game}"
        response = requests.get(url)
        
        if response.status_code == 200:
            results.append(response.json())
    
    return results if results else [{"Game": "N/A", "Moneyline": "N/A", "Spread": "N/A", "O/U": "N/A"}]

# **Fetch Player Stats & Best Bets**
def fetch_player_data(player_name):
    try:
        player = commonplayerinfo.CommonPlayerInfo(player_name=player_name).get_dict()
        stats = player["resultSets"][0]["rowSet"]
        
        if stats:
            return [{"Category": stat[0], "Value": stat[1]} for stat in stats]
        else:
            return None
    except:
        return None
