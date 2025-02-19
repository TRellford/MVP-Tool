import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import scoreboardv2, commonteamroster
import datetime

from nba_api.stats.endpoints import ScoreboardV2
import datetime

def fetch_games():
    games = scoreboardv2.ScoreboardV2().get_dict()["resultSets"][0]["rowSet"]
    
    game_list = []
    for game in games:
        home_team = game[6]  # Home team abbreviation (correct index)
        away_team = game[7]  # Away team abbreviation (correct index)
        game_list.append(f"{away_team} vs {home_team}")  # Correct format
    
    return game_list  # Now returns "CHA vs LAL" instead of "20250219/CHALAL"
    
### **🔹 Fetch Up-to-Date NBA Rosters**
def fetch_rosters(team_id):
    """
    Gets the latest roster for a given team.
    """
    roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_dict()
    players = roster_data["resultSets"][0]["rowSet"]
    
    return {player[3]: player[2] for player in players}  # Returns {Player Name: Position}


### **🔹 Scrape Live FanDuel Player Props**
def fetch_props(game_url):
    """
    Scrapes FanDuel for real-time player props for a given NBA game.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(game_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    
    props = []
    for prop_section in soup.find_all("div", class_="player-prop-class"):  
        try:
            player = prop_section.find("span", class_="player-name-class").text.strip()
            stat = prop_section.find("span", class_="stat-category-class").text.strip()
            line = prop_section.find("span", class_="prop-line-class").text.strip()
            odds = prop_section.find("span", class_="odds-class").text.strip()

            props.append({
                "player": player,
                "prop": f"{stat} Over/Under {line}",
                "odds": odds
            })
        except AttributeError:
            continue  # Skips any missing data errors

    return props


### **🔹 Fetch Moneyline, Spread, & Over/Under**
def fetch_ml_spread_ou():
    """
    Gets the latest Moneyline, Spread, and O/U totals from sportsbooks.
    """
    # Example URL (Replace with an actual sportsbook odds provider)
    url = "https://www.example.com/nba-odds"  
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching odds: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    
    odds_data = {}
    for game_section in soup.find_all("div", class_="game-odds-class"):  
        try:
            teams = game_section.find("span", class_="team-names-class").text.strip()
            ml = game_section.find("span", class_="moneyline-class").text.strip()
            spread = game_section.find("span", class_="spread-class").text.strip()
            total = game_section.find("span", class_="ou-class").text.strip()

            odds_data[teams] = {"ML": ml, "Spread": spread, "Total": total}
        except AttributeError:
            continue

    return odds_data


### **🔹 Fetch Individual Player Data (Last 10 Games)**
def fetch_player_data(player_id):
    """
    Gets the last 10 games of player data.
    """
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching player data: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    
    stats = []
    for row in soup.find_all("tr")[:10]:  # Only last 10 games
        try:
            date = row.find("td", {"data-stat": "date_game"}).text.strip()
            points = row.find("td", {"data-stat": "pts"}).text.strip()
            assists = row.find("td", {"data-stat": "ast"}).text.strip()
            rebounds = row.find("td", {"data-stat": "trb"}).text.strip()

            stats.append({"Date": date, "PTS": points, "AST": assists, "REB": rebounds})
        except AttributeError:
            continue

    return stats
