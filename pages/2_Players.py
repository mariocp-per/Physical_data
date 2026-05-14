# pages/2_Players.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from database.player_repository import (
    get_players
)

from database.db import get_connection

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
# LOAD DATA
# =========================

conn = get_connection()

coros_df = pd.read_sql_query(
    """
    SELECT *
    FROM coros_data
    WHERE player_id = ?
    """,
    conn,
    params=(player_id,)
)

myzone_df = pd.read_sql_query(
    """
    SELECT *
    FROM myzone_data
    WHERE player_id = ?
    """,
    conn,
    params=(player_id,)
)

suunto_df = pd.read_sql_query(
    """
    SELECT *
    FROM suunto_data
    WHERE player_id = ?
    """,
    conn,
    params=(player_id,)
)

conn.close()

# =========================
# HISTORICAL METRICS
# =========================

all_hr = []
all_speed = []

# COROS

if not coros_df.empty:

    if "heart_rate" in coros_df.columns:

        all_hr.extend(
            coros_df["heart_rate"]
            .dropna()
            .tolist()
        )

    if "speed" in coros_df.columns:

        all_speed.extend(
            (
                coros_df["speed"]
                .dropna() * 3.6
            ).tolist()
        )

# MYZONE

if not myzone_df.empty:

    if "heart_rate" in myzone_df.columns:

        all_hr.extend(
            myzone_df["heart_rate"]
            .dropna()
            .tolist()
        )

# SUUNTO

if not suunto_df.empty:

    if "heart_rate" in suunto_df.columns:

        all_hr.extend(
            suunto_df["heart_rate"]
            .dropna()
            .tolist()
        )

    if "speed" in suunto_df.columns:

        all_speed.extend(
            (
                suunto_df["speed"]
                .dropna() * 3.6
            ).tolist()
        )

historical_hr_max = None
historical_hr_mean = None
historical_speed_max = None

if len(all_hr) > 0:

    historical_hr_max = int(
        max(all_hr)
    )

    historical_hr_mean = round(
        sum(all_hr) / len(all_hr),
        1
    )

if len(all_speed) > 0:

    historical_speed_max = round(
        max(all_speed),
        2
    )

# =========================
# TOTAL SESSIONS
# =========================

total_sessions = 0

if not coros_df.empty:

    total_sessions += (
        coros_df["session_id"]
        .nunique()
    )

if not myzone_df.empty:

    total_sessions += (
        myzone_df["session_id"]
        .nunique()
    )

if not suunto_df.empty:

    total_sessions += (
        suunto_df["session_id"]
        .nunique()
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

# =========================
# ZONES
# =========================

if historical_hr_max is not None:

    st.subheader("Tiempo en zonas")

    z1 = historical_hr_max * 0.60
    z2 = historical_hr_max * 0.70
    z3 = historical_hr_max * 0.80
    z4 = historical_hr_max * 0.90

    zones = {
        "Z1": 0,
        "Z2": 0,
        "Z3": 0,
        "Z4": 0,
        "Z5": 0
    }

    def process_hr(df, sample_seconds):

        if df.empty:

            return

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

    process_hr(
        coros_df,
        1
    )

    process_hr(
        suunto_df,
        1
    )

    process_hr(
        myzone_df,
        60
    )

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
SELECT
    da.session_id,
    da.player_id,
    da.device_type as device,
    MAX(c.timestamp) as session_date
FROM device_assignments da
LEFT JOIN coros_data c
    ON da.session_id = c.session_id
    AND da.player_id = c.player_id
WHERE da.player_id = 3
AND da.device_type = 'COROS'
GROUP BY
    da.session_id,
    da.player_id,
    da.device_type

UNION ALL

SELECT
    da.session_id,
    da.player_id,
    da.device_type as device,
    MAX(m.timestamp) as session_date
FROM device_assignments da
LEFT JOIN myzone_data m
    ON da.session_id = m.session_id
    AND da.player_id = m.player_id
WHERE da.player_id = 3
AND da.device_type = 'MYZONE'
GROUP BY
    da.session_id,
    da.player_id,
    da.device_type

UNION ALL

SELECT
    da.session_id,
    da.player_id,
    da.device_type as device,
    MAX(s.timestamp) as session_date
FROM device_assignments da
LEFT JOIN suunto_data s
    ON da.session_id = s.session_id
    AND da.player_id = s.player_id
WHERE da.player_id = 3
AND da.device_type = 'SUUNTO'
GROUP BY
    da.session_id,
    da.player_id,
    da.device_type

ORDER BY session_date DESC;
"""

sessions_df = pd.read_sql_query(
    sessions_query,
    conn,
    params=(
        player_id,
        player_id,
        player_id
    )
)

conn.close()

# =========================
# DATES
# =========================

sessions_df["session_date"] = pd.to_datetime(
    sessions_df["session_date"],
    errors="coerce"
)

sessions_df = sessions_df.dropna(
    subset=["session_date"]
)

sessions_df = sessions_df.sort_values(
    "session_date",
    ascending=False
)

# =========================
# LABELS
# =========================

sessions_df["label"] = (
    sessions_df["device"]
    + " | "
    + sessions_df["session_id"].astype(str)
    + " | "
    + sessions_df["session_date"]
        .dt.strftime("%d/%m %H:%M")
)

# =========================
# DEFAULT LAST 2
# =========================

default_sessions = (
    sessions_df["label"]
    .head(2)
    .tolist()
)

selected_labels = st.multiselect(
    "Seleccionar sesiones",
    sessions_df["label"].tolist(),
    default=default_sessions
)

selected_sessions_df = sessions_df[
    sessions_df["label"]
    .isin(selected_labels)
]

if selected_sessions_df.empty:

    st.stop()

# =========================
# LOAD TIMELINE DATA
# =========================

conn = get_connection()

# COROS

coros_timeline = pd.DataFrame()

selected_coros = selected_sessions_df[
    selected_sessions_df["device"] == "COROS"
]["session_id"].tolist()

if len(selected_coros) > 0:

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
            ["?"] * len(selected_coros)
        )
    )

    coros_params = [
        player_id
    ] + selected_coros

    coros_timeline = pd.read_sql_query(
        coros_query,
        conn,
        params=coros_params
    )

    coros_timeline["device"] = "COROS"

# MYZONE

myzone_timeline = pd.DataFrame()

selected_myzone = selected_sessions_df[
    selected_sessions_df["device"] == "MYZONE"
]["session_id"].tolist()

if len(selected_myzone) > 0:

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
            ["?"] * len(selected_myzone)
        )
    )

    myzone_params = [
        player_id
    ] + selected_myzone

    myzone_timeline = pd.read_sql_query(
        myzone_query,
        conn,
        params=myzone_params
    )

    myzone_timeline["device"] = "MYZONE"

# SUUNTO

suunto_timeline = pd.DataFrame()

selected_suunto = selected_sessions_df[
    selected_sessions_df["device"] == "SUUNTO"
]["session_id"].tolist()

if len(selected_suunto) > 0:

    suunto_query = """
    SELECT
        timestamp,
        session_id,
        heart_rate,
        speed,
        distance
    FROM suunto_data
    WHERE player_id = ?
    AND session_id IN ({})
    ORDER BY timestamp
    """.format(
        ",".join(
            ["?"] * len(selected_suunto)
        )
    )

    suunto_params = [
        player_id
    ] + selected_suunto

    suunto_timeline = pd.read_sql_query(
        suunto_query,
        conn,
        params=suunto_params
    )

    suunto_timeline["device"] = "SUUNTO"

conn.close()

# =========================
# COMBINE DATA
# =========================

timeline_df = pd.concat(
    [
        coros_timeline,
        myzone_timeline,
        suunto_timeline
    ],
    ignore_index=True
)

if timeline_df.empty:

    st.info(
        "No hay datos disponibles"
    )

    st.stop()

timeline_df["timestamp"] = pd.to_datetime(
    timeline_df["timestamp"],
    errors="coerce"
)

timeline_df = timeline_df.dropna(
    subset=["timestamp"]
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
    "black",
    "brown",
    "pink"
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

for idx, (_, row) in enumerate(
    selected_sessions_df.iterrows()
):

    session = row["session_id"]

    device = row["device"]

    session_df = timeline_df[
        (
            timeline_df["session_id"] == session
        )
        &
        (
            timeline_df["device"] == device
        )
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
        label=row["label"],
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

speed_df = timeline_df[
    timeline_df["device"].isin(
        ["COROS", "SUUNTO"]
    )
].copy()

if (
    not speed_df.empty
    and "speed" in speed_df.columns
):

    st.subheader(
        "Velocidad"
    )

    fig_speed, ax_speed = plt.subplots(
        figsize=(14, 5)
    )

    for idx, (_, row) in enumerate(
        selected_sessions_df.iterrows()
    ):

        session = row["session_id"]

        device = row["device"]

        session_df = speed_df[
            (
                speed_df["session_id"] == session
            )
            &
            (
                speed_df["device"] == device
            )
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

        session_df["speed_kmh"] = (
            session_df["speed"] * 3.6
        )

        ax_speed.plot(
            session_df["minutes"],
            session_df["speed_kmh"],
            label=row["label"],
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

distance_df = timeline_df[
    timeline_df["device"].isin(
        ["COROS", "SUUNTO"]
    )
].copy()

if (
    not distance_df.empty
    and "distance" in distance_df.columns
):

    st.subheader(
        "Distancia acumulada"
    )

    fig_dist, ax_dist = plt.subplots(
        figsize=(14, 5)
    )

    for idx, (_, row) in enumerate(
        selected_sessions_df.iterrows()
    ):

        session = row["session_id"]

        device = row["device"]

        session_df = distance_df[
            (
                distance_df["session_id"] == session
            )
            &
            (
                distance_df["device"] == device
            )
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

        session_df["distance_km"] = (
            session_df["distance"] / 1000
        )

        ax_dist.plot(
            session_df["minutes"],
            session_df["distance_km"],
            label=row["label"],
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