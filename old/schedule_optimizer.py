# import streamlit as st
# import pandas as pd
# import pulp

# # -----------------------------
# # Load team data
# # -----------------------------
# st.title("Softball Schedule Optimizer")

# st.markdown("""
# **NCAA Softball RPI Notes:**
# - Home wins count as **0.7** wins.
# - Away wins count as **1.3** wins.
# - Neutral site wins count as **1.0** wins.
# - These adjustments apply to WP, OWP, and OOWP.
# - A maximum of 3 games per opponent is allowed.
# - RPI calculation weights:
#     - 0.25 × Team Win Percentage (WP)
#     - 0.50 × Opponents' Win Percentage (OWP)
#     - 0.25 × Opponents' Opponents' Win Percentage (OOWP)
# """)

# teams_df = pd.read_csv("data/softball_2025_rpi.csv")  # Use RPI from actual game results

# user_team = 'Georgia Tech'
# user_rpi = teams_df.loc[teams_df['team'] == user_team, 'RPI'].values[0] if user_team in teams_df['team'].values else 0.5

# # Estimate win probability based only on RPI difference
# teams_df['win_prob'] = 1 / (1 + 10 ** ((teams_df['RPI'] - user_rpi) / 0.1))

# teams = teams_df['team'].tolist()
# RPI = dict(zip(teams_df['team'], teams_df['RPI']))
# win_prob = dict(zip(teams_df['team'], teams_df['win_prob']))

# # List of conference teams to exclude
# conference_teams = ['Duke', 'Florida State', 'Clemson', 'Virginia Tech', 'Wake Forest', 'Louisville', 'North Carolina', 'Pittsburgh', 'Syracuse', 'Virginia', 'NC State', 'Miami', 'Boston College']
# opponents = [team for team in teams if team != 'Georgia Tech' and team not in conference_teams]

# # -----------------------------
# # Streamlit Sidebar Inputs
# # -----------------------------
# st.sidebar.header("Scheduling Parameters")
# N = st.sidebar.number_input("Total number of games", value=30, min_value=1, max_value=50)
# ALPHA = st.sidebar.slider("Weight on RPI vs Win Prob", min_value=0.0, max_value=1.0, value=0.75, step=0.05)

# # Manual override selector
# selected_team = st.sidebar.selectbox("Select a team to set an override:", ["None"] + sorted(opponents))
# override_location = st.sidebar.selectbox("Game location: (home/away/neutral)", ["home", "away", "neutral"])
# override_count = st.sidebar.selectbox("Set games (or exclude):", ["No Override", "0 (Exclude)", "1", "2", "3"])

# if 'manual_games' not in st.session_state:
#     st.session_state.manual_games = {}
# if 'manual_exclude' not in st.session_state:
#     st.session_state.manual_exclude = set()

# if st.sidebar.button("Save Override"):
#     override_msg = None
#     if selected_team and selected_team != "None":
#         override_msg = f"Override saved for {selected_team}."
#     if override_msg:
#         st.sidebar.success(override_msg)
#         if override_count == "0 (Exclude)":
#             st.session_state.manual_exclude.add(selected_team)
#             st.session_state.manual_games.pop(selected_team, None)
#         elif override_count in ["1", "2", "3"]:
#             st.session_state.manual_games[selected_team] = (override_location, int(override_count))
#             st.session_state.manual_exclude.discard(selected_team)
#         elif override_count == "No Override":
#             st.session_state.manual_games.pop(selected_team, None)
#             st.session_state.manual_exclude.discard(selected_team)

# # Reset overrides button
# if st.sidebar.button("Reset All Overrides"):
#     st.session_state.manual_games = {}
#     st.session_state.manual_exclude = set()

# # -----------------------------
# # Run optimization
# # -----------------------------
# if st.sidebar.button("Optimize Schedule"):

#     model = pulp.LpProblem("Maximize_Adjusted_RPI", pulp.LpMaximize)

#     # Separate variables for home, away, neutral games
#     x_home = pulp.LpVariable.dicts("home_games", opponents, lowBound=0, upBound=3, cat='Integer')
#     x_away = pulp.LpVariable.dicts("away_games", opponents, lowBound=0, upBound=3, cat='Integer')
#     x_neutral = pulp.LpVariable.dicts("neutral_games", opponents, lowBound=0, upBound=3, cat='Integer')

#     # Objective function: use RPI and win prob, apply value weights (not adjust win prob directly)
#     model += pulp.lpSum(
#         x_home[i] * ((ALPHA * RPI[i]) + (1 - ALPHA) * 0.7 * win_prob[i]) +
#         x_away[i] * ((ALPHA * RPI[i]) + (1 - ALPHA) * 1.3 * win_prob[i]) +
#         x_neutral[i] * ((ALPHA * RPI[i]) + (1 - ALPHA) * 1.0 * win_prob[i])
#         for i in opponents
#     ), "Blended_RPI_WinProb_With_Weighted_Wins"

#     # Constraints
#     model += pulp.lpSum(x_home[i] + x_away[i] + x_neutral[i] for i in opponents) == N, "Total_Games"
#     for i in opponents:
#         model += x_home[i] + x_away[i] + x_neutral[i] <= 3, f"Max3PerTeam_{i}"

#     for team, (loc, val) in st.session_state.manual_games.items():
#         if team in opponents:
#             if loc == "home":
#                 model += x_home[team] == val, f"ManualHomeGames_{team}"
#             elif loc == "away":
#                 model += x_away[team] == val, f"ManualAwayGames_{team}"
#             elif loc == "neutral":
#                 model += x_neutral[team] == val, f"ManualNeutralGames_{team}"
#     for team in st.session_state.manual_exclude:
#         if team in opponents:
#             model += x_home[team] + x_away[team] + x_neutral[team] == 0, f"ExcludeTeam_{team}"

#     model.solve(pulp.PULP_CBC_CMD(msg=0))

#     result_data = []
#     for team in opponents:
#         h = int(pulp.value(x_home[team]))
#         a = int(pulp.value(x_away[team]))
#         n = int(pulp.value(x_neutral[team]))
#         total = h + a + n
#         if total > 0:
#             result_data.append({
#                 'Team': team,
#                 'Home Games': h,
#                 'Away Games': a,
#                 'Neutral Games': n,
#                 'Total Games': total,
#                 'RPI': RPI[team],
#                 'Win Prob': win_prob[team]
#             })

#     results_df = pd.DataFrame(result_data)
#     st.subheader("Optimized Schedule")
#     st.dataframe(results_df)
