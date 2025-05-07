import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os

# -----------------------------------
# 1. Detect local vs public API
# -----------------------------------
def detect_api_base():
    try:
        response = requests.get("http://localhost:3000/schedule/softball/d1/2025/03", timeout=2)
        if response.status_code == 200:
            print("✅ Using local NCAA API at http://localhost:3000")
            return "http://localhost:3000"
    except:
        pass
    print("🌐 Using public NCAA API at https://ncaa-api.henrygd.me")
    return "https://ncaa-api.henrygd.me"

BASE_URL = detect_api_base()

# -----------------------------------
# 2. Fetch games from API
# -----------------------------------
def get_scoreboard_data(year: int, month: int, day: int):
    url = f"{BASE_URL}/scoreboard/softball/d1/{year}/{month:02d}/{day:02d}/all-conf"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        return data.get("games", []) if isinstance(data, dict) else []
    except:
        return []

# -----------------------------------
# 3. Extract game results
# -----------------------------------
def extract_game_results(raw_games):
    records = []
    for item in raw_games:
        game = item.get("game", {})
        if game.get("gameState") != "final":
            continue

        home = game.get("home", {})
        away = game.get("away", {})

        home_team = home.get("names", {}).get("short")
        away_team = away.get("names", {}).get("short")

        try:
            home_score = int(home.get("score", -1))
            away_score = int(away.get("score", -1))
        except:
            continue

        if home_score == -1 or away_score == -1 or home_score == away_score:
            continue

        winner = home_team if home_score > away_score else away_team
        loser = away_team if home_score > away_score else home_team

        records.append({"team": winner, "opponent": loser, "result": "W"})
        records.append({"team": loser, "opponent": winner, "result": "L"})
    return records

# -----------------------------------
# 4. Compute WP, OWP, OOWP, RPI
# -----------------------------------
def compute_rpi_components(game_df):
    teams = game_df['team'].unique()
    wp_dict, owp_dict, oowp_dict = {}, {}, {}

    for team in teams:
        games = game_df[game_df["team"] == team]
        wins = (games["result"] == "W").sum()
        total = len(games)
        wp_dict[team] = wins / total if total > 0 else 0.0

    for team in teams:
        opps = game_df[game_df["team"] == team]["opponent"]
        opp_wps = []
        for opp in opps:
            opp_games = game_df[(game_df["team"] == opp) & (game_df["opponent"] != team)]
            opp_wins = (opp_games["result"] == "W").sum()
            opp_total = len(opp_games)
            if opp_total > 0:
                opp_wps.append(opp_wins / opp_total)
        owp_dict[team] = sum(opp_wps) / len(opp_wps) if opp_wps else 0.0

    for team in teams:
        opps = game_df[game_df["team"] == team]["opponent"]
        opp_owps = [owp_dict.get(opp, 0.0) for opp in opps]
        oowp_dict[team] = sum(opp_owps) / len(opp_owps) if opp_owps else 0.0

    return pd.DataFrame([{
        "team": team,
        "WP": wp_dict[team],
        "OWP": owp_dict[team],
        "OOWP": oowp_dict[team],
        "RPI": 0.25 * wp_dict[team] + 0.50 * owp_dict[team] + 0.25 * oowp_dict[team]
    } for team in teams])

# -----------------------------------
# 5. Main logic
# -----------------------------------
def main():
    print("📡 Starting RPI scrape for 2025...")
    season_start = datetime(2025, 2, 1)
    season_end = datetime(2025, 5, 15)
    chunk_size = 7
    all_games = []

    current_date = season_start
    while current_date <= season_end:
        for i in range(chunk_size):
            date = current_date + timedelta(days=i)
            if date > season_end:
                break
            raw_games = get_scoreboard_data(date.year, date.month, date.day)
            day_results = extract_game_results(raw_games)
            all_games.extend(day_results)
            time.sleep(1)  # prevent API spam
        current_date += timedelta(days=chunk_size)

    print(f"✅ Pulled {len(all_games)} game results.")
    os.makedirs("data", exist_ok=True)
    games_df = pd.DataFrame(all_games)
    games_df.to_csv("data/softball_2025_results.csv", index=False)

    rpi_df = compute_rpi_components(games_df)

    # Calculate Georgia Tech win probabilities using RPI-based logistic model
    gt_rpi = rpi_df.loc[rpi_df["team"] == "Georgia Tech", "RPI"].values[0]
    rpi_df["win_prob_vs_GT"] = 1 / (1 + 10 ** ((rpi_df["RPI"] - gt_rpi) * 10))  # 10 = scaling factor

    rpi_df.to_csv("data/softball_2025_stats.csv", index=False)
    print("📁 Saved RPI and Georgia Tech win probabilities to data/softball_2025_stats.csv")

if __name__ == "__main__":
    main()
