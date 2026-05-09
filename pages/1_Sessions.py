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
)
ORDER BY p.surname
"""

players_df = pd.read_sql_query(
    players_query,
    conn,
    params=(
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
# HR COMPARISON
# =========================

st.header(
    "Comparador FC"
)

coros_query = """
SELECT
    cd.timestamp,
    cd.heart_rate,
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

# =========================
# PRIORIDAD COROS
# =========================

coros_players = set(
    coros_df["player_id"].unique()
)

myzone_filtered = myzone_df[
    ~myzone_df["player_id"].isin(
        coros_players
    )
]

hr_df = pd.concat(
    [
        coros_df,
        myzone_filtered
    ],
    ignore_index=True
)

conn.close()


# =========================
# VALIDATION
# =========================

if hr_df.empty:

    st.info(
        "No hay datos cardíacos"
    )

else:

    # =========================
    # PLAYER OPTIONS
    # =========================

    hr_df["player_name"] = (
        hr_df["surname"] +
        ", " +
        hr_df["name"]
    )

    player_options = sorted(
        hr_df["player_name"].unique()
    )

    c1, c2 = st.columns(2)

    with c1:

        player_1 = st.selectbox(
            "Jugadora 1",
            player_options,
            index=0
        )

    with c2:

        default_index = (
            1 if len(player_options) > 1
            else 0
        )

        player_2 = st.selectbox(
            "Jugadora 2",
            player_options,
            index=default_index
        )

    # =========================
    # FILTER PLAYERS
    # =========================

    player_1_df = hr_df[
        hr_df["player_name"] == player_1
    ].copy()

    player_2_df = hr_df[
        hr_df["player_name"] == player_2
    ].copy()

    # =========================
    # TIMESTAMP
    # =========================

    player_1_df["timestamp"] = (
        pd.to_datetime(
            player_1_df["timestamp"]
        )
        .dt.tz_localize(None)
    )

    player_2_df["timestamp"] = (
        pd.to_datetime(
            player_2_df["timestamp"]
        )
        .dt.tz_localize(None)
    )

    # =========================
    # NORMALIZE TIME
    # =========================

    start_time = min(
        player_1_df["timestamp"].min(),
        player_2_df["timestamp"].min()
    )

    player_1_df["minutes"] = (
        player_1_df["timestamp"] - start_time
    ).dt.total_seconds() / 60

    player_2_df["minutes"] = (
        player_2_df["timestamp"] - start_time
    ).dt.total_seconds() / 60

    # =========================
    # PLOT
    # =========================

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    ax.plot(
        player_1_df["minutes"],
        player_1_df["heart_rate"],
        label=player_1,
        linewidth=2
    )

    ax.plot(
        player_2_df["minutes"],
        player_2_df["heart_rate"],
        label=player_2,
        linewidth=2
    )

    ax.set_xlabel(
        "Minutos"
    )

    ax.set_ylabel(
        "FC"
    )

    ax.set_title(
        "Comparativa frecuencia cardíaca"
    )

    ax.legend()

    ax.grid(True)

    st.pyplot(fig)