sync def fetch_games(day_offset=0):
    """
    Fetches NBA games for today (default) or tomorrow (if day_offset=1).
    Returns a list of games formatted as "TEAM1 v TEAM2".
    """
    try:
        selected_date = (datetime.today() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        url = f"https://api.nba.com/schedule?date={selected_date}"  # Ensure correct API

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"API Error: {response.status}")
                    return []

                data = await response.json()

        if "games" not in data or not data["games"]:
            return []

        # ✅ Fix incorrect team names
        games_list = []
        for game in data["games"]:
            away_team = game["awayTeam"]["teamTricode"]  # Example: CHA
            home_team = game["homeTeam"]["teamTricode"]  # Example: LAL
            matchup = f"{away_team} v {home_team}"
            games_list.append(matchup)

        return games_list

    except Exception as e:
        print(f"Error fetching games: {str(e)}")
        return []
