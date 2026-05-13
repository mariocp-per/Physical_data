# pages/1_Sessions.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from database.db import get_connection


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Sesiones",
    layout="wide"
)

st.title("📅 Sesiones")


# =========================
# LOAD SESSIONS
# =========================

conn = get_connection()

sessions_query = """
SELECT *
FROM training_sessions
ORDER BY session_date DESC
"""

sessions_df = pd.read_sql_query(
    sessions_query,
    conn
)

if sessions_df.empty:

    st.warning(
        "No hay sesiones"
    )

    st.stop()


# =========================
# SESSION SELECTOR
# =========================

session_options = {
    f"{row['session_date']} - {row['location']}": row["id"]
    for _, row in sessions_df.iterrows()
}

selected_session = st.selectbox(
    "Seleccionar sesión",
    list(session_options.keys())
)

session_id = session_options[
    selected_session
]

session_row = sessions_df[
    sessions_df["id"] == session_id
].iloc[0]


# =========================
# SESSION INFO
# =========================

st.header(
    "Información sesión"
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Fecha",
    str(session_row["session_date"])
)

c2.metric(
    "Lugar",
    session_row["location"]
)

c3.metric(
    "Asistentes",
    session_row["attendees"]
)

c4.metric(
    "Partido",
    "Sí" if session_row["flg_game"] == 1
    else "No"
)

c5.metric(
    "ID",
    session_row["id"]
)


# =========================
# NOTES
# =========================

if pd.notna(session_row["notes"]):

    st.info(
        session_row["notes"]
    )


# =========================
# LOAD PLAYERS
# =========================

players_query = """
SELECT DISTINCT
    p.id,
    p.name,
    p.surname
FROM players p
WHERE p.id IN (

    SELECT player_id
    FROM coros_data
    WHERE session_id = ?

    UNION

    SELECT player_id
    FROM myzone_data
    WHERE session_id = ?

    UNION

    SELECT player_id
    FROM suunto_data
    WHERE session_id = ?

)
ORDER BY p.surname
"""

players_df = pd.read_sql_query(
    players_query,
    conn,
    params=(
        session_id,
        session_id,
        session_id
    )
)


# =========================
# PLAYER LIST
# =========================

st.header(
    "Jugadoras registradas"
)

if not players_df.empty:

    players_df["player"] = (
        players_df["surname"] +
        ", " +
        players_df["name"]
    )

    st.dataframe(
        players_df[
            ["player"]
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No hay jugadoras registradas"
    )


# =========================
# COMPARADOR
# =========================

st.header(
    "Comparador"
)


# =========================
# COROS
# =========================

coros_query = """
SELECT
    cd.timestamp,
    cd.heart_rate,
    cd.distance,
    cd.speed,
    p.name,
    p.surname,
    p.id as player_id,
    'COROS' as source
FROM coros_data cd
JOIN players p
    ON cd.player_id = p.id
WHERE cd.session_id = ?
"""

coros_df = pd.read_sql_query(
    coros_query,
    conn,
    params=(session_id,)
)


# =========================
# MYZONE
# =========================

myzone_query = """
SELECT
    md.timestamp,
    md.heart_rate,
    p.name,
    p.surname,
    p.id as player_id,
    'MYZONE' as source
FROM myzone_data md
JOIN players p
    ON md.player_id = p.id
WHERE md.session_id = ?
"""

myzone_df = pd.read_sql_query(
    myzone_query,
    conn,
    params=(session_id,)
)

# MYZONE NO TIENE DISTANCIA NI VELOCIDAD
myzone_df["distance"] = None
myzone_df["speed"] = None


# =========================
# SUUNTO
# =========================

suunto_query = """
SELECT
    sd.timestamp,
    sd.heart_rate,
    sd.distance,
    sd.speed,
    p.name,
    p.surname,
    p.id as player_id,
    'SUUNTO' as source
FROM suunto_data sd
JOIN players p
    ON sd.player_id = p.id
WHERE sd.session_id = ?
"""

suunto_df = pd.read_sql_query(
    suunto_query,
    conn,
    params=(session_id,)
)


# =========================
# COMBINE DATA
# =========================

hr_df = pd.concat(
    [
        coros_df,
        suunto_df,
        myzone_df
    ],
    ignore_index=True
)

conn.close()


# =========================
# VALIDATION
# =========================

if hr_df.empty:

    st.info(
        "No hay datos"
    )

    st.stop()


# =========================
# PLAYER NAME
# =========================

hr_df["player_name"] = (
    hr_df["surname"] +
    ", " +
    hr_df["name"] +
    " (" +
    hr_df["source"] +
    ")"
)


# =========================
# TIMESTAMP
# =========================

hr_df["timestamp"] = pd.to_datetime(
    hr_df["timestamp"],
    errors="coerce"
)

# eliminar timestamps inválidos
hr_df = hr_df.dropna(
    subset=["timestamp"]
)


# =========================
# PLAYER SELECTOR
# =========================

player_options = sorted(
    hr_df["player_name"].unique()
)

selected_players = st.multiselect(
    "Seleccionar jugadoras/dispositivos",
    player_options,
    default=player_options[:2],
    max_selections=3
)

if len(selected_players) == 0:

    st.warning(
        "Selecciona al menos una jugadora"
    )

    st.stop()


# =========================
# HEART RATE FIGURE
# =========================

st.subheader(
    "Frecuencia cardíaca"
)

fig_hr, ax_hr = plt.subplots(
    figsize=(14, 6)
)


# =========================
# SPEED FIGURE
# =========================

st.subheader(
    "Velocidad"
)

fig_speed, ax_speed = plt.subplots(
    figsize=(14, 6)
)


# =========================
# DISTANCE FIGURE
# =========================

st.subheader(
    "Distancia"
)

fig_dist, ax_dist = plt.subplots(
    figsize=(14, 6)
)


# =========================
# LOOP PLAYERS
# =========================

for player in selected_players:

    player_df = hr_df[
        hr_df["player_name"] == player
    ].copy()

    if player_df.empty:
        continue

    player_df = player_df.sort_values(
        "timestamp"
    )

    # =========================
    # NORMALIZE TIME
    # =========================

    start_time = player_df[
        "timestamp"
    ].min()

    player_df["minutes"] = (
        player_df["timestamp"] - start_time
    ).dt.total_seconds() / 60

    # =========================
    # HEART RATE
    # =========================

    if player_df["heart_rate"].notna().any():

        ax_hr.plot(
            player_df["minutes"],
            player_df["heart_rate"],
            label=player,
            linewidth=2
        )

    # =========================
    # SPEED
    # =========================

    if (
        "speed" in player_df.columns and
        player_df["speed"].notna().any()
    ):

        ax_speed.plot(
            player_df["minutes"],
            player_df["speed"],
            label=player,
            linewidth=2
        )

    # =========================
    # DISTANCE
    # =========================

    if (
        "distance" in player_df.columns and
        player_df["distance"].notna().any()
    ):

        ax_dist.plot(
            player_df["minutes"],
            player_df["distance"],
            label=player,
            linewidth=2
        )


# =========================
# FORMAT HR
# =========================

ax_hr.set_xlabel(
    "Minutos"
)

ax_hr.set_ylabel(
    "FC"
)

ax_hr.set_title(
    "Comparativa frecuencia cardíaca"
)

ax_hr.legend()

ax_hr.grid(True)

st.pyplot(fig_hr)


# =========================
# FORMAT SPEED
# =========================

ax_speed.set_xlabel(
    "Minutos"
)

ax_speed.set_ylabel(
    "Velocidad"
)

ax_speed.set_title(
    "Comparativa velocidad"
)

ax_speed.legend()

ax_speed.grid(True)

st.pyplot(fig_speed)


# =========================
# FORMAT DISTANCE
# =========================

ax_dist.set_xlabel(
    "Minutos"
)

ax_dist.set_ylabel(
    "Distancia"
)

ax_dist.set_title(
    "Comparativa distancia"
)

ax_dist.legend()

ax_dist.grid(True)

st.pyplot(fig_dist)