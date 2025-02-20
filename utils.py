import time
import json
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.endpoints import playergamelog
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests

# ✅ Configure Selenium WebDriver for Scraping Sportsbook Odds
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")


# ✅ 1️⃣ Async Fetch NBA Games (Today or Tomorrow)
sync def fetch_games(day_offset=0):
    """
    Fetches NBA games for today (default) or tomorrow (if day_offset=1).
    """
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        url = f"https://www.nba.com/schedule?date={selected_date}"  # Update API if needed

        print(f"Fetching games for: {selected_date}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"API Error: {response.status}")
                    return []

                data = await response.json()
                print("Raw API Response:", data)

        if "games" not in data or not data["games"]:
            return []

        return [(game["gameId"], f"{game['visitor']} vs {game['home']}") for game in data["games"]]

    except Exception as e:
        print(f"Error fetching games: {str(e)}")
        return []


# ✅ 2️⃣ Async Fetch Last 10 Games + Opponent Matchups
async def fetch_recent_player_stats(player_id, opponent_abbreviation=None):
    """
    Fetches last 10 games stats for a player and previous matchups vs. today's opponent.
    """
    try:
        game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24").get_data_frames()[0]
        last_10_games = game_log.head(10)

        # If opponent_abbreviation is provided, filter previous matchups
        prev_matchups = game_log[game_log["MATCHUP"].str.contains(opponent_abbreviation, na=False)] if opponent_abbreviation else pd.DataFrame()

        return last_10_games, prev_matchups

    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

def fetch_ml_spread_ou(game_id):
    """
    Scrapes sportsbook for Moneyline, Spread, and Over/Under odds for a given game.
    """
    try:
        sportsbook_url = f"https://www.fanduel.com/sportsbook/nba/{game_id}"  # Update URL if needed
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(sportsbook_url, headers=headers)

        if response.status_code != 200:
            return f"Error: Failed to fetch odds. Status Code: {response.status_code}"

        # Parse JSON response (update based on sportsbook API structure)
        data = response.json()
        if "odds" not in data:
            return f"Error: Unexpected JSON format - missing 'odds' key"

        return data["odds"]

    except Exception as e:
        return f"Error fetching ML/Spread/O/U odds: {str(e)}"
        
# ✅ 3️⃣ Web Scraping: Fetch Live Moneyline, Spread, Over/Under Odds
def scrape_sportsbook_odds():
    """
    Uses Selenium & BeautifulSoup to scrape live sportsbook odds.
    """
    try:
        sportsbook_url = "https://www.fanduel.com/sportsbook/nba"  # Replace with actual sportsbook URL
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        driver.get(sportsbook_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        odds_data = {}
        games = soup.find_all("div", class_="game-module")  # Adjust based on sportsbook structure

        for game in games:
            teams = game.find_all("div", class_="team-name")
            moneyline = game.find_all("span", class_="moneyline")
            spread = game.find_all("span", class_="spread")
            over_under = game.find_all("span", class_="over-under")

            if teams and moneyline and spread and over_under:
                matchup = f"{teams[0].text.strip()} vs {teams[1].text.strip()}"
                odds_data[matchup] = {
                    "Moneyline": [moneyline[0].text.strip(), moneyline[1].text.strip()],
                    "Spread": [spread[0].text.strip(), spread[1].text.strip()],
                    "Over/Under": [over_under[0].text.strip(), over_under[1].text.strip()]
                }

        return odds_data

    except Exception as e:
        return {}


# ✅ 4️⃣ Web Scraping: Fetch Player Props
def fetch_props(player_name):
    """
    Scrapes sportsbook for player prop bets.
    """
    try:
        sportsbook_url = f"https://www.fanduel.com/sportsbook/nba/player-props?search={player_name.replace(' ', '+')}"
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        driver.get(sportsbook_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        props_data = {}
        props = soup.find_all("div", class_="prop-module")

        for prop in props:
            category = prop.find("div", class_="prop-category").text.strip()
            line = prop.find("span", class_="prop-line").text.strip()
            odds = prop.find("span", class_="prop-odds").text.strip()
            props_data[category] = f"{line} ({odds})"

        return props_data

    except Exception as e:
        return {}


# ✅ 5️⃣ Streamlit UI for Game Selection
import streamlit as st
import asyncio

def show_game_selection_ui():
    """
    Displays a Streamlit UI for selecting today's or tomorrow's NBA games.
    """
    st.title("NBA Games Schedule")

    # ✅ **Fix: Ensure radio buttons actually appear**
    selected_option = st.radio("Select Date:", ["Today's Games", "Tomorrow's Games"], index=0)

    # ✅ **Fix: Fetch games synchronously using `asyncio.run()`**
    if selected_option == "Today's Games":
        games = asyncio.run(fetch_games(0))  # Fetch today's games
    else:
        games = asyncio.run(fetch_games(1))  # Fetch tomorrow's games

    # ✅ **Fix: Ensure dropdown updates dynamically**
    if games:
        game_options = {matchup: game_id for game_id, matchup in games}
        selected_game = st.selectbox("Choose a game:", list(game_options.keys()))

        st.write(f"**You selected:** {selected_game}")

    else:
        st.write("No games scheduled for this date.")

# ✅ 6️⃣ Streamlit UI for Player Search
def show_player_search_ui():
    """
    Displays a Streamlit UI for searching NBA player stats and props.
    """
    st.title("NBA Player Search & Props")

    player_name = st.text_input("Enter Player Name:")
    if player_name:
        st.subheader("Last 10 Games")
        stats, prev_matchups = asyncio.run(fetch_recent_player_stats(1234, "LAL"))  # Replace with actual player ID
        if not stats.empty:
            st.dataframe(stats)
        else:
            st.write("No game data available.")

        st.subheader("Player Prop Bets")
        props = scrape_player_props(player_name)
        st.write(props if props else "No props found.")

async def load_games():
    today_games = await fetch_games(0)  # ✅ Use 'await' since it's an async function
    print(today_games)  # ✅ This will correctly print the game list

asyncio.run(load_games())  # ✅ Run the async function properly

# ✅ Run Streamlit UI
if __name__ == "__main__":
    st.sidebar.title("NBA Betting Tool")
    page = st.sidebar.selectbox("Choose a Page:", ["Game Schedule", "Player Search"])
    if page == "Game Schedule":
        show_game_selection_ui()
    elif page == "Player Search":
        show_player_search_ui()
