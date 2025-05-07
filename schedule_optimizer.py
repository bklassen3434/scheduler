import streamlit as st
import pandas as pd

# -----------------------------
# Load NCAA Stats (still needed)
# -----------------------------
stats_df = pd.read_csv("data/softball_2025_stats.csv")

# -----------------------------
# Constants
# -----------------------------
location_multiplier = {
    "home": 0.7,
    "away": 1.3,
    "neutral": 1.0
}

# -----------------------------
# RPI Calculation
# -----------------------------
def calculate_rpi(schedule: pd.DataFrame) -> float:
    if schedule.empty:
        return 0.0
    merged = schedule.merge(stats_df, how="left", left_on="opponent", right_on="team")
    merged["adj_win"] = merged["win_prob_vs_GT"] * merged["location"].map(location_multiplier)
    WP = merged["adj_win"].mean()
    OWP = merged["OWP"].mean()
    OOWP = merged["OOWP"].mean()
    rpi = 0.25 * WP + 0.50 * OWP + 0.25 * OOWP
    return round(rpi, 4)

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🧮 Softball RPI What-If Simulator")
st.markdown("Manually enter games to build a schedule and calculate your **expected RPI**.")

# -----------------------------
# Initialize session schedule
# -----------------------------
if "schedule" not in st.session_state:
    st.session_state.schedule = pd.DataFrame(columns=["opponent", "location"])

# -----------------------------
# Display current schedule and RPI
# -----------------------------
st.subheader("📅 Current Schedule")
st.dataframe(st.session_state.schedule)

current_rpi = calculate_rpi(st.session_state.schedule)
st.metric("📈 Expected RPI", current_rpi)

# -----------------------------
# Unified Add/Remove Interface
# -----------------------------
st.subheader("🎛️ Modify Schedule")

mode = st.radio("Choose an action", ["Add Game", "Remove Game"], horizontal=True)

if mode == "Add Game":
    col1, col2 = st.columns(2)
    with col1:
        team = st.selectbox("Opponent", sorted(stats_df["team"].unique()), key="add_team")
    with col2:
        location = st.selectbox("Location", ["home", "away", "neutral"], key="add_location")
    
    if st.button("Apply Change", key="add_btn"):
        st.session_state.schedule = pd.concat([
            st.session_state.schedule,
            pd.DataFrame([{"opponent": team, "location": location}])
        ], ignore_index=True)
        st.success(f"✅ Added game vs {team} ({location})")

elif mode == "Remove Game":
    options = [f"{i}: {row['opponent']} ({row['location']})"
               for i, row in st.session_state.schedule.iterrows()]
    if options:
        selected = st.selectbox("Select game to remove", options, key="remove_select")
        idx = int(selected.split(":")[0])
        if st.button("Apply Change", key="remove_btn"):
            st.session_state.schedule = st.session_state.schedule.drop(idx).reset_index(drop=True)
            st.success("🗑️ Game removed.")

# -----------------------------
# Download Schedule
# -----------------------------
if not st.session_state.schedule.empty:
    st.download_button(
        label="📥 Download Schedule CSV",
        data=st.session_state.schedule.to_csv(index=False),
        file_name="simulated_schedule.csv",
        mime="text/csv"
    )
