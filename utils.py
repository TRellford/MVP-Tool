import requests
from nba_api.stats.endpoints import scoreboardv2, commonteamroster
from datetime import datetime
from bs4 import BeautifulSoup

# ✅ Fetch live NBA games for today
def fetch_games():
    today = datetime.today().strftime('%Y-%m-%d')
    try:
        games = scoreboardv2.ScoreboardV2(game_date=today).get_dict()["gameHeader"]
        return [f"{game['visitorTeamAbbreviation']} vs {game['homeTeamAbbreviation']}" for game in games]
    except Exception as e:
        print(f"Error fetching games: {e}")
        return []

# ✅ Fetch up-to-date rosters from NBA API
def fetch_roster(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_dict()["resultSets"][0]["rowSet"]
        return [{"Player": player[3], "Position": player[5], "Jersey": player[2]} for player in roster]
    except Exception as e:
        print(f"Error fetching roster: {e}")
        return []

# ✅ Fetch real-time betting odds from FanDuel/DraftKings
def fetch_odds():
    url = "https://www.fanduel.com/nba"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        odds_data = []
        for game in soup.find_all("div", class_="event"):
            teams = game.find_all("span", class_="team-name")
            odds = game.find_all("span", class_="odds")
            
            if len(teams) == 2 and len(odds) >= 2:
                matchup = f"{teams[0].text} vs {teams[1].text}"
                odds_data.append({"Matchup": matchup, "Odds": [odds[0].text, odds[1].text]})

        return odds_data
    except Exception as e:
        print(f"Error fetching odds: {e}")
        return []

# ✅ Fetch latest injury reports from ESPN
def fetch_injuries():
    url = "https://www.espn.com/nba/injuries"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        injuries = []
        for row in soup.find_all("tr", class_="Table__TR"):
            cols = row.find_all("td")
            if len(cols) >= 3:
                team = cols[0].text.strip()
                player = cols[1].text.strip()
                status = cols[2].text.strip()
                injuries.append({"Team": team, "Player": player, "Status": status})

        return injuries
    except Exception as e:
        print(f"Error fetching injuries: {e}")
        return []

# ✅ Fetch historical data for last 10 games
def fetch_player_stats(player_id):
    url = f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        stats = []
        table = soup.find("table", {"id": "per_game"})
        if table:
            rows = table.find_all("tr")[-10:]  # Last 10 games
            for row in rows:
                cols = row.find_all("td")
                if cols:
                    game_date = cols[0].text.strip()
                    points = cols[1].text.strip()
                    assists = cols[2].text.strip()
                    rebounds = cols[3].text.strip()
                    stats.append({"Date": game_date, "PTS": points, "AST": assists, "REB": rebounds})

        return stats
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return []

# ✅ Fetch first basket probabilities
def fetch_first_basket_data():
    url = "https://www.nba.com/stats/teams/traditional/?sort=FGM&dir=-1"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        first_basket_data = []
        for row in soup.find_all("tr", class_="Table__TR"):
            cols = row.find_all("td")
            if len(cols) >= 5:
                team = cols[0].text.strip()
                first_fgm = cols[2].text.strip()
                first_attempts = cols[3].text.strip()
                first_basket_data.append({"Team": team, "First Basket %": first_fgm, "Attempts": first_attempts})

        return first_basket_data
    except Exception as e:
        print(f"Error fetching first basket data: {e}")
        return []
