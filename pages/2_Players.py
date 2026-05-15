# pages/2_Players.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.patches import (
    Rectangle
)

from database.player_repository import (
    get_players
)

from database.db import (
    get_connection
)

from metrics.player_profile import (
    get_player_hr_profile
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

    st.warning(
        "No hay jugadoras"
    )

    st.stop()

# =========================
# PLAYER SELECTOR
# =========================

player_options = {
    f"{row['surname']}, {row['name']}": row["id"]
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

st.header(
    "Información personal"
)

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
# LOAD RAW DATA
# =========================

conn = get_connection()

coros_df = pd.read_sql_query(
    f"""
    SELECT *
    FROM coros_data
    WHERE player_id = {player_id}
    """,
    conn
)

myzone_df = pd.read_sql_query(
    f"""
    SELECT *
    FROM myzone_data
    WHERE player_id = {player_id}
    """,
    conn
)

suunto_df = pd.read_sql_query(
    f"""
    SELECT *
    FROM suunto_data
    WHERE player_id = {player_id}
    """,
    conn
)

# =========================
# PLAYER HR PROFILE
# =========================

profile = get_player_hr_profile(
    player_id
)

# =========================
# HISTORICAL METRICS
# =========================

all_hr = []
all_speed = []

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

if not myzone_df.empty:

    if "heart_rate" in myzone_df.columns:

        all_hr.extend(
            myzone_df["heart_rate"]
            .dropna()
            .tolist()
        )

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

# =========================
# HR PROFILE
# =========================

if profile is not None:

    historical_hr_max = int(
        profile["hr_max"]
    )

    z1 = profile["zones"]["z1"]
    z2 = profile["zones"]["z2"]
    z3 = profile["zones"]["z3"]
    z4 = profile["zones"]["z4"]

# =========================
# HR MEAN
# =========================

if len(all_hr) > 0:

    historical_hr_mean = round(
        sum(all_hr) / len(all_hr),
        1
    )

# =========================
# SPEED MAX
# =========================

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

st.header(
    "Métricas"
)

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
# ZONES
# =========================

if profile is not None:

    st.subheader(
        "Tiempo en zonas"
    )

    zones = {
        "Z1": 0,
        "Z2": 0,
        "Z3": 0,
        "Z4": 0,
        "Z5": 0
    }

    def process_hr(
        df,
        sample_seconds
    ):

        if df.empty:

            return

        for hr in df[
            "heart_rate"
        ].dropna():

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

    # =========================
    # TOTAL TIME
    # =========================

    total_seconds = sum(
        zones.values()
    )

    # =========================
    # ZONES DF
    # =========================

    zones_df = pd.DataFrame({

        "Zona": list(
            zones.keys()
        ),

        "% Minutos": [

            round(
                (
                    v / total_seconds
                ) * 100,
                1
            )

            if total_seconds > 0
            else 0

            for v in zones.values()
        ]
    })

    ranges = {

        "Z1": f"< {int(z1)}",

        "Z2": (
            f"{int(z1)} - "
            f"{int(z2)}"
        ),

        "Z3": (
            f"{int(z2)} - "
            f"{int(z3)}"
        ),

        "Z4": (
            f"{int(z3)} - "
            f"{int(z4)}"
        ),

        "Z5": f"> {int(z4)}"
    }

    zones_df["Rango BPM"] = (
        zones_df["Zona"]
        .map(ranges)
    )

    zones_df = zones_df[
        [
            "Zona",
            "Rango BPM",
            "% Minutos"
        ]
    ]

    st.dataframe(
        zones_df,
        use_container_width=True
    )