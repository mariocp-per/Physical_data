# pages/2_Players.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from database.player_repository import (
    get_players
)

from database.db import get_connection

from metrics.hr_metrics import (
    build_hr_summary
)

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Jugadoras",
    layout="wide"
)

st.title("👥 Jugadoras")

# =========================
# LOAD PLAYERS
# =========================

players = get_players()

if players.empty:

    st.warning("No hay jugadoras")

    st.stop()

# =========================
# PLAYER SELECTOR
# =========================

player_options = {
    f"{row['surname']}, {row['name']}": row['id']
    for _, row in players.iterrows()
}

selected_player = st.selectbox(
    "Seleccionar jugadora",
    list(player_options.keys())
)

player_id = player_options[
    selected_player
]

# =========================
# PLAYER INFO
# =========================

player_row = players[
    players["id"] == player_id
].iloc[0]

st.header("Información personal")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Nombre",
    player_row["name"]
)

c2.metric(
    "Apellido",
    player_row["surname"]
)

c3.metric(
    "Categoría",
    player_row["category"]
)

c4.metric(
    "Dorsal",
    player_row["dorsal"]
)

# =========================
# LOAD PLAYER DATA
# =========================

conn = get_connection()

query_coros = """
SELECT *
FROM coros_data
WHERE player_id = ?
"""

coros_df = pd.read_sql_query(
    query_coros,
    conn,
    params=(player_id,)
)

query_myzone = """
SELECT *
FROM myzone_data
WHERE player_id = ?
"""

myzone_df = pd.read_sql_query(
    query_myzone,
    conn,
    params=(player_id,)
)

conn.close()

# =========================
# SESSION COUNTS
# =========================

coros_sessions = 0
myzone_sessions = 0

if not coros_df.empty:

    coros_sessions = (
        coros_df["session_id"]
        .nunique()
    )

if not myzone_df.empty:

    myzone_sessions = (
        myzone_df["session_id"]
        .nunique()
    )

total_sessions = max(
    coros_sessions,
    myzone_sessions
)

# =========================
# HISTORICAL METRICS
# =========================

historical_hr_max = None
historical_hr_mean = None
historical_speed_max = None

if not coros_df.empty:

    # FC MAX HISTÓRICA
    historical_hr_max = int(
        coros_df["heart_rate"].max()
    )

    # FC MEDIA TODAS LAS SESIONES
    historical_hr_mean = round(
        coros_df["heart_rate"].mean(),
        1
    )

    # VELOCIDAD MÁXIMA HISTÓRICA
    if "speed" in coros_df.columns:

        # COROS viene en m/s -> km/h
        historical_speed_max = round(
            coros_df["speed"].max() * 3.6,
            2
        )

elif not myzone_df.empty:

    historical_hr_max = int(
        myzone_df["heart_rate"].max()
    )

    historical_hr_mean = round(
        myzone_df["heart_rate"].mean(),
        1
    )

# =========================
# METRICS
# =========================

st.header("Métricas")

if historical_hr_max is not None:

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "FC máxima histórica",
        historical_hr_max
    )

    m2.metric(
        "FC media",
        historical_hr_mean
    )

    m3.metric(
        "Velocidad máxima",
        (
            f"{historical_speed_max} km/h"
            if historical_speed_max is not None
            else "-"
        )
    )

    m4.metric(
        "Sesiones",
        total_sessions
    )

else:

    st.info(
        "No hay datos monitorizados"
    )

# =========================
# ZONES BASED ON HISTORICAL HR MAX
# =========================

if historical_hr_max is not None:

    z1 = historical_hr_max * 0.60
    z2 = historical_hr_max * 0.70
    z3 = historical_hr_max * 0.80
    z4 = historical_hr_max * 0.90

    def calculate_zones(df, sample_seconds):

        zones = {
            "Z1": 0,
            "Z2": 0,
            "Z3": 0,
            "Z4": 0,
            "Z5": 0
        }

        for hr in df["heart_rate"].dropna():

            if hr < z1:

                zones["Z1"] += sample_seconds

            elif hr < z2:

                zones["Z2"] += sample_seconds

            elif hr < z3:

                zones["Z3"] += sample_seconds

            elif hr < z4:

                zones["Z4"] += sample_seconds

            else:

                zones["Z5"] += sample_seconds

        zones_df = pd.DataFrame({
            "Zona": list(zones.keys()),
            "Minutos": [
                round(v / 60, 1)
                for v in zones.values()
            ]
        })

        ranges = {
            "Z1": f"< {int(z1)}",
            "Z2": f"{int(z1)} - {int(z2)}",
            "Z3": f"{int(z2)} - {int(z3)}",
            "Z4": f"{int(z3)} - {int(z4)}",
            "Z5": f"> {int(z4)}"
        }

        zones_df["Rango BPM"] = (
            zones_df["Zona"]
            .map(ranges)
        )

        return zones_df[
            [
                "Zona",
                "Rango BPM",
                "Minutos"
            ]
        ]

    st.subheader("Tiempo en zonas")

    if not coros_df.empty:

        zones_df = calculate_zones(
            coros_df,
            sample_seconds=1
        )

    else:

        zones_df = calculate_zones(
            myzone_df,
            sample_seconds=60
        )

    st.dataframe(
        zones_df,
        use_container_width=True
    )

# =========================
# SESSION SELECTOR
# =========================

st.header("Comparación de sesiones")

conn = get_connection()

sessions_query = """
SELECT DISTINCT session_id
FROM coros_data
WHERE player_id = ?

UNION

SELECT DISTINCT session_id
FROM myzone_data
WHERE player_id = ?

ORDER BY session_id DESC
"""

sessions_df = pd.read_sql_query(
    sessions_query,
    conn,
    params=(
        player_id,
        player_id
    )
)

available_sessions = sessions_df[
    "session_id"
].tolist()

selected_sessions = st.multiselect(
    "Seleccionar sesiones",
    available_sessions,
    default=available_sessions[:3]
)

conn.close()

if len(selected_sessions) == 0:

    st.stop()

# =========================
# LOAD TIMELINE DATA
# =========================

conn = get_connection()

coros_query = """
SELECT
    timestamp,
    session_id,
    heart_rate,
    speed,
    distance
FROM coros_data
WHERE player_id = ?
AND session_id IN ({})
ORDER BY timestamp
""".format(
    ",".join(
        ["?"] * len(selected_sessions)
    )
)

coros_params = [
    player_id
] + selected_sessions

coros_timeline = pd.read_sql_query(
    coros_query,
    conn,
    params=coros_params
)

myzone_query = """
SELECT
    timestamp,
    session_id,
    heart_rate
FROM myzone_data
WHERE player_id = ?
AND session_id IN ({})
ORDER BY timestamp
""".format(
    ",".join(
        ["?"] * len(selected_sessions)
    )
)

myzone_params = [
    player_id
] + selected_sessions

myzone_timeline = pd.read_sql_query(
    myzone_query,
    conn,
    params=myzone_params
)

conn.close()

# =========================
# PRIORIDAD COROS
# =========================

if not coros_timeline.empty:

    timeline_df = coros_timeline.copy()

    sample_seconds = 1

    source = "coros"

else:

    timeline_df = myzone_timeline.copy()

    sample_seconds = 60

    source = "myzone"

# =========================
# VALIDATION
# =========================

if timeline_df.empty:

    st.info(
        "No hay datos"
    )

    st.stop()

timeline_df["timestamp"] = (
    pd.to_datetime(
        timeline_df["timestamp"]
    )
    .dt.tz_localize(None)
)

# =========================
# COLORS
# =========================

session_colors = [
    "blue",
    "red",
    "green",
    "orange",
    "purple",
    "black"
]

# =========================
# HR GRAPH
# =========================

st.subheader(
    "Frecuencia cardíaca"
)

fig_hr, ax_hr = plt.subplots(
    figsize=(14, 5)
)

for idx, session in enumerate(selected_sessions):

    session_df = timeline_df[
        timeline_df["session_id"] == session
    ].copy()

    if session_df.empty:

        continue

    session_df = session_df.sort_values(
        "timestamp"
    )

    start_time = session_df[
        "timestamp"
    ].min()

    session_df["minutes"] = (
        session_df["timestamp"] - start_time
    ).dt.total_seconds() / 60

    ax_hr.plot(
        session_df["minutes"],
        session_df["heart_rate"],
        label=f"Sesión {session}",
        linewidth=2,
        color=session_colors[
            idx % len(session_colors)
        ]
    )

ax_hr.set_xlabel("Minutos")
ax_hr.set_ylabel("FC")
ax_hr.grid(True)
ax_hr.legend()

st.pyplot(fig_hr)

# =========================
# SPEED GRAPH
# =========================

if (
    source == "coros"
    and "speed" in timeline_df.columns
):

    st.subheader(
        "Velocidad"
    )

    fig_speed, ax_speed = plt.subplots(
        figsize=(14, 5)
    )

    for idx, session in enumerate(selected_sessions):

        session_df = timeline_df[
            timeline_df["session_id"] == session
        ].copy()

        if session_df.empty:

            continue

        session_df = session_df.sort_values(
            "timestamp"
        )

        start_time = session_df[
            "timestamp"
        ].min()

        session_df["minutes"] = (
            session_df["timestamp"] - start_time
        ).dt.total_seconds() / 60

        # m/s -> km/h
        session_df["speed_kmh"] = (
            session_df["speed"] * 3.6
        )

        ax_speed.plot(
            session_df["minutes"],
            session_df["speed_kmh"],
            label=f"Sesión {session}",
            linewidth=2,
            color=session_colors[
                idx % len(session_colors)
            ]
        )

    ax_speed.set_xlabel("Minutos")
    ax_speed.set_ylabel("km/h")
    ax_speed.grid(True)
    ax_speed.legend()

    st.pyplot(fig_speed)

# =========================
# DISTANCE GRAPH
# =========================

if (
    source == "coros"
    and "distance" in timeline_df.columns
):

    st.subheader(
        "Distancia acumulada"
    )

    fig_dist, ax_dist = plt.subplots(
        figsize=(14, 5)
    )

    for idx, session in enumerate(selected_sessions):

        session_df = timeline_df[
            timeline_df["session_id"] == session
        ].copy()

        if session_df.empty:

            continue

        session_df = session_df.sort_values(
            "timestamp"
        )

        start_time = session_df[
            "timestamp"
        ].min()

        session_df["minutes"] = (
            session_df["timestamp"] - start_time
        ).dt.total_seconds() / 60

        # metros -> km
        session_df["distance_km"] = (
            session_df["distance"] / 1000
        )

        ax_dist.plot(
            session_df["minutes"],
            session_df["distance_km"],
            label=f"Sesión {session}",
            linewidth=2,
            color=session_colors[
                idx % len(session_colors)
            ]
        )

    ax_dist.set_xlabel("Minutos")
    ax_dist.set_ylabel("Kilómetros")
    ax_dist.grid(True)
    ax_dist.legend()

    st.pyplot(fig_dist)