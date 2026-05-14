# pages/4_AI_Analysis.py

import streamlit as st
import sqlite3
import pandas as pd

from metrics.session_metrics import build_player_session_metrics

# =========================================================
# CONFIG
# =========================================================

DB_PATH = "BT_db.db"

st.set_page_config(
    page_title="AI Analysis",
    page_icon="🧠",
    layout="wide"
)

# =========================================================
# DB
# =========================================================

@st.cache_data
def get_sessions():

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        id,
        session_date,
        location,
        flg_game
    FROM training_sessions
    ORDER BY session_date DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


@st.cache_data
def get_players_by_session(session_id):

    conn = sqlite3.connect(DB_PATH)

    query = f"""
    SELECT DISTINCT
        p.id,
        p.name,
        p.surname,
        p.dorsal

    FROM device_assignments da

    INNER JOIN players p
        ON p.id = da.player_id

    WHERE da.session_id = {session_id}

    ORDER BY p.surname
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# =========================================================
# IA FUNCTIONS
# =========================================================

def calculate_intensity(metrics):

    score = 0

    # FC
    if metrics["avg_hr"] >= 170:
        score += 40

    elif metrics["avg_hr"] >= 155:
        score += 30

    elif metrics["avg_hr"] >= 140:
        score += 20

    else:
        score += 10

    # Distance
    if metrics["total_distance"] >= 7000:
        score += 30

    elif metrics["total_distance"] >= 5000:
        score += 20

    else:
        score += 10

    # Speed
    if metrics["max_speed"] >= 24:
        score += 30

    elif metrics["max_speed"] >= 20:
        score += 20

    else:
        score += 10

    return min(score, 100)


def classify_intensity(score):

    if score >= 80:
        return "Very High"

    elif score >= 60:
        return "High"

    elif score >= 40:
        return "Moderate"

    return "Low"


def detect_fatigue(metrics):

    if (
        metrics["avg_hr"] > 165
        and metrics["max_speed"] < 18
    ):
        return "High"

    elif metrics["avg_hr"] > 150:
        return "Moderate"

    return "Low"


def generate_summary(metrics, intensity, fatigue):

    text = f"""
### Session Summary

**{metrics['name']} {metrics['surname']}**

- Average HR: {metrics['avg_hr']} bpm
- Max HR: {metrics['max_hr']} bpm
- Total Distance: {metrics['total_distance']} m
- Max Speed: {metrics['max_speed']} km/h
- Sprint Count: {metrics['sprint_count']}

The session intensity was classified as **{intensity}**.

Fatigue detection level: **{fatigue}**.
"""

    if intensity == "Very High":
        text += """

The player was exposed to a very demanding cardiovascular load.
"""

    if fatigue == "High":
        text += """

Possible neuromuscular fatigue detected.
"""

    return text


def generate_recommendation(intensity, fatigue):

    if intensity == "Very High" and fatigue == "High":

        return """
- Recovery session recommended
- Sleep monitoring advised
- Hydration control
- Monitor next 48h load
"""

    elif intensity in ["High", "Very High"]:

        return """
- Monitor recovery status
- Maintain hydration
- Control accumulated weekly load
"""

    return """
- Normal readiness status
- Standard recovery protocol
"""


# =========================================================
# HEADER
# =========================================================

st.title("🧠 AI Session Analysis")

st.markdown("""
Automatic interpretation of physiological and GPS performance data.
""")

# =========================================================
# SESSION SELECTOR
# =========================================================

sessions_df = get_sessions()

if sessions_df.empty:

    st.warning("No sessions available")
    st.stop()

selected_session = st.selectbox(
    "Select Session",
    sessions_df["id"],
    format_func=lambda x:
        f"Session {x} - "
        f"{sessions_df[sessions_df['id'] == x]['session_date'].values[0]}"
)

# =========================================================
# PLAYER SELECTOR
# =========================================================

players_df = get_players_by_session(selected_session)

if players_df.empty:

    st.warning("No players assigned to this session")
    st.stop()

selected_player = st.selectbox(
    "Select Player",
    players_df["id"],
    format_func=lambda x:
        f"{players_df[players_df['id'] == x]['surname'].values[0]}, "
        f"{players_df[players_df['id'] == x]['name'].values[0]}"
)

# =========================================================
# BUILD METRICS
# =========================================================

metrics = build_player_session_metrics(
    selected_session,
    selected_player
)

if metrics is None:

    st.error("No metrics available")
    st.stop()

# =========================================================
# AI ANALYSIS
# =========================================================

intensity_score = calculate_intensity(metrics)

intensity = classify_intensity(intensity_score)

fatigue = detect_fatigue(metrics)

summary = generate_summary(
    metrics,
    intensity,
    fatigue
)

recommendation = generate_recommendation(
    intensity,
    fatigue
)

# =========================================================
# TOP METRICS
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Intensity",
        intensity,
        intensity_score
    )

with col2:
    st.metric(
        "Fatigue",
        fatigue
    )

with col3:
    st.metric(
        "Distance",
        f"{metrics['total_distance']} m"
    )

with col4:
    st.metric(
        "Max Speed",
        f"{metrics['max_speed']} km/h"
    )

# =========================================================
# SUMMARY
# =========================================================

st.subheader("📝 AI Summary")

st.markdown(summary)

# =========================================================
# RECOMMENDATION
# =========================================================

st.subheader("📋 Recommendation")

st.success(recommendation)

# =========================================================
# HR ZONES
# =========================================================

st.subheader("❤️ Heart Rate Zones")

zones_df = pd.DataFrame({
    "Zone": list(metrics["hr_zones"].keys()),
    "Samples": list(metrics["hr_zones"].values())
})

st.bar_chart(
    zones_df.set_index("Zone")
)

# =========================================================
# RAW METRICS
# =========================================================

with st.expander("View Full Metrics"):

    st.json(metrics)

# =========================================================
# FUTURE
# =========================================================

st.divider()

st.subheader("🚀 Next Evolution")

st.markdown("""
Future AI modules:

- Injury risk
- ACWR
- Readiness score
- Tactical heatmaps
- Position comparison
- Weekly load monitoring
- AI coach assistant
- Session classification
""")