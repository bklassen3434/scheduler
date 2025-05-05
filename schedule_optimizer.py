import streamlit as st
import pandas as pd
import pulp

# -----------------------------
# Load team data
# -----------------------------
st.title("Softball Schedule Optimizer")

teams_df = pd.read_csv("data/cleaned_data.csv")

teams_df['rpi'] = (teams_df['rpi_ranking'].max() - teams_df['rpi_ranking'] + 1) / teams_df['rpi_ranking'].max()

user_team = 'Georgia Tech'
user_elo = teams_df.loc[teams_df['team'] == user_team, 'elo'].values[0] if user_team in teams_df['team'].values else 1500
teams_df['win_prob'] = 1 / (1 + 10 ** ((teams_df['elo'] - user_elo) / 400))

teams = teams_df['team'].tolist()
RPI = dict(zip(teams_df['team'], teams_df['rpi']))
win_prob = dict(zip(teams_df['team'], teams_df['win_prob']))

# -----------------------------
# Streamlit Sidebar Inputs
# -----------------------------
st.sidebar.header("Scheduling Parameters")
N = st.sidebar.number_input("Total number of games", value=10, min_value=1, max_value=50)
ALPHA = st.sidebar.slider("Weight on RPI vs Win Prob", min_value=0.0, max_value=1.0, value=0.5, step=0.05)

st.sidebar.header("Manual Override Selector")
selected_team = st.sidebar.selectbox("Select a team to set an override:", ["None"] + teams)
override_value = st.sidebar.selectbox("Set games (or exclude):", ["No Override", "0 (Exclude)", "1", "2", "3"])

# Store overrides in session state
if 'manual_games' not in st.session_state:
    st.session_state.manual_games = {}
if 'manual_exclude' not in st.session_state:
    st.session_state.manual_exclude = set()

# Add save override button
if st.sidebar.button("Save Override") and selected_team != "None":
    if override_value == "0 (Exclude)":
        st.session_state.manual_exclude.add(selected_team)
        st.session_state.manual_games.pop(selected_team, None)
    elif override_value in ["1", "2", "3"]:
        st.session_state.manual_games[selected_team] = int(override_value)
        st.session_state.manual_exclude.discard(selected_team)
    elif override_value == "No Override":
        st.session_state.manual_games.pop(selected_team, None)
        st.session_state.manual_exclude.discard(selected_team)

# Display current manual settings
st.sidebar.markdown("---")
st.sidebar.subheader("Current Overrides")
if st.session_state.manual_games:
    st.sidebar.write("**Fixed Games:**")
    for team, val in st.session_state.manual_games.items():
        st.sidebar.write(f"{team}: {val} games")
if st.session_state.manual_exclude:
    st.sidebar.write("**Excluded Teams:**")
    for team in st.session_state.manual_exclude:
        st.sidebar.write(f"{team}")

# Reset overrides button
if st.sidebar.button("Reset All Overrides"):
    st.session_state.manual_games = {}
    st.session_state.manual_exclude = set()

# -----------------------------
# Run optimization
# -----------------------------
if st.sidebar.button("Optimize Schedule"):

    model = pulp.LpProblem("Maximize_Adjusted_ELO", pulp.LpMaximize)

    opponents = [team for team in teams if team != 'Georgia Tech']
    x = pulp.LpVariable.dicts("games", opponents, lowBound=0, upBound=3, cat='Integer')

    # Objective: Blended RPI and Win Probability
    model += pulp.lpSum(x[i] * ((ALPHA * RPI[i]) + ((1 - ALPHA) * win_prob[i])) for i in opponents), "Blended_RPI_WinProb"

    # Constraints
    model += pulp.lpSum(x[i] for i in opponents) == N, "Total_Games"
    for i in opponents:
        model += x[i] <= 3, f"Max3PerTeam_{i}"

    for team, val in st.session_state.manual_games.items():
        if team in opponents:
            model += x[team] == val, f"ManualGames_{team}"
    for team in st.session_state.manual_exclude:
        if team in opponents:
            model += x[team] == 0, f"ExcludeTeam_{team}"

    model.solve(pulp.PULP_CBC_CMD(msg=0))

    result_data = []
    for team in opponents:
        g = int(pulp.value(x[team]))
        if g > 0:
            result_data.append({
                'Team': team,
                'Games': g,
                'RPI': RPI[team],
                'Win Prob': win_prob[team]
            })

    results_df = pd.DataFrame(result_data)
    st.subheader("Optimized Schedule")
    st.dataframe(results_df)
