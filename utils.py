from nba_api.stats.endpoints import scoreboardv2, playergamelogs, commonplayerinfo
import requests
import datetime, timedelta

def fetch_games(date_choice="Today"):
    """
    Fetches NBA games for today or tomorrow.
    :param date_choice: "Today" or "Tomorrow"
    :return: List of games formatted as "AwayTeam vs HomeTeam"
    """
    try:
        # Get NBA game data
        scoreboard = scoreboardv2.ScoreboardV2()
        games = scoreboard.get_dict()['resultSets'][0]['rowSet']

        game_list = []
        today_date = datetime.now().strftime("%Y-%m-%d")
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        for game in games:
            game_date = game[0]  # Extract the game date
            away_team = game[7]  # Away team abbreviation
            home_team = game[6]  # Home team abbreviation

            if (date_choice == "Today" and game_date == today_date) or \
               (date_choice == "Tomorrow" and game_date == tomorrow_date):
                game_list.append(f"{away_team} vs {home_team}")

        return game_list if game_list else ["No Games Found"]
    
    except Exception as e:
        return [f"Error fetching games: {str(e)}"]

# **Fetch Player Props**
def fetch_props(selected_games):
    props = []
    for game in selected_games:
        game_data = get_game_data(game)  # Ensure this function is working properly
        for player in game_data['players']:
            props.append({
                "Player": player["name"],
                "Prop": player["best_bet"],
                "Odds": player["odds"],
                "Confidence": player["confidence_score"]
            })
    return props

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
