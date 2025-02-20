import streamlit as st
from utils import fetch_games, fetch_props, fetch_ml_spread_ou, fetch_recent_player_stats

st.set_page_config(page_title="MVP Tool", layout="wide")

# UI Layout
st.title("MVP Sports Betting Tool 🚀")
st.sidebar.header("Game Selection")

# Toggle Features
sgp_toggle = st.sidebar.checkbox("Enable Same Game Parlay (SGP)")
sgp_plus_toggle = st.sidebar.checkbox("Enable SGP+ (Multiple Games)")
ml_toggle = st.sidebar.checkbox("Include Moneyline/Spread/O/U")

# Game Selection
selected_games = st.sidebar.multiselect("Select Games:", fetch_games())

# Prop Selection
prop_count = st.sidebar.slider("Number of Props Per Game", 1, 8, 4)

# Risk Level Selection
risk_level = st.sidebar.selectbox("Select Risk Level:", ["Very Safe", "Safe", "Moderate", "High Risk"])

# Fetch Predictions
if st.sidebar.button("Get Predictions"):
    if ml_toggle:
        ml_results = fetch_ml_spread_ou(selected_games)
        st.subheader("Moneyline, Spread & Over/Under Predictions")
        st.table(ml_results)

    if selected_games:
        props = fetch_props(selected_games, prop_count, risk_level, sgp_toggle, sgp_plus_toggle)
        st.subheader("Top Player Props")
        st.table(props)

# Player Search
# Ensure fetch_player_data is properly imported

st.sidebar.header("Player Search")
player_name = st.sidebar.text_input("Enter Player Name")

if st.sidebar.button("Search"):
    player_info = fetch_player_data(player_name)  # ✅ Fetch player data

    if "error" in player_info:
        st.error(player_info["error"])  # ✅ Display error message if player not found
    else:
        st.subheader(f"Player Analysis: {player_name}")

        # ✅ Display Player Profile Info (excluding last_10_games)
        profile_data = {k: v for k, v in player_info.items() if k != "last_10_games"}
        st.table(pd.DataFrame([profile_data]))  # Convert single dictionary to DataFrame

        # ✅ Display Last 10 Games Stats (Fixing Type Issues)
        if "last_10_games" in player_info and isinstance(player_info["last_10_games"], list):
            st.subheader(f"Last 10 Games Stats for {player_name}")

            # 🔹 Fix Data Type Issue by Converting all to String
            games_df = pd.DataFrame(player_info["last_10_games"])
            games_df = games_df.astype(str)  # Convert all columns to string to avoid ArrowTypeError
            st.table(games_df)
    # ✅ Display Last 10 Games in a Separate Table
    if "last_10_games" in player_info and isinstance(player_info["last_10_games"], list):
        st.subheader(f"Last 10 Games Stats for {player_name}")
        st.table(pd.DataFrame(player_info["last_10_games"]))  # ✅ Convert list of dicts to DataFrame
