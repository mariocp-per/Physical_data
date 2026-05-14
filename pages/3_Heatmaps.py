# pages/3_Heatmaps.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.patches import (
    Rectangle,
    Circle,
    Arc
)

from database.db import get_connection


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Heatmaps",
    layout="wide"
)

st.title("🔥 Heatmaps")


# =========================
# DRAW COURT
# =========================

def draw_court(ax):

    court_length = 28
    court_width = 15

    # OUTER COURT
    outer = Rectangle(
        (0, 0),
        court_length,
        court_width,
        linewidth=2,
        color="black",
        fill=False,
        zorder=10
    )

    ax.add_patch(outer)

    # MIDLINE
    ax.plot(
        [court_length / 2,
         court_length / 2],
        [0, court_width],
        color="black",
        zorder=10
    )

    # CENTER CIRCLE
    center_circle = Circle(
        (
            court_length / 2,
            court_width / 2
        ),
        1.8,
        linewidth=2,
        color="black",
        fill=False,
        zorder=10
    )

    ax.add_patch(center_circle)

    # PAINT
    paint_width = 4.9
    paint_height = 5.8

    left_paint = Rectangle(
        (
            0,
            (court_width - paint_height) / 2
        ),
        paint_width,
        paint_height,
        linewidth=2,
        color="black",
        fill=False,
        zorder=10
    )

    right_paint = Rectangle(
        (
            court_length - paint_width,
            (court_width - paint_height) / 2
        ),
        paint_width,
        paint_height,
        linewidth=2,
        color="black",
        fill=False,
        zorder=10
    )

    ax.add_patch(left_paint)
    ax.add_patch(right_paint)

    # HOOPS
    left_hoop = Circle(
        (
            1.575,
            court_width / 2
        ),
        0.225,
        linewidth=2,
        color="black",
        fill=False,
        zorder=10
    )

    right_hoop = Circle(
        (
            court_length - 1.575,
            court_width / 2
        ),
        0.225,
        linewidth=2,
        color="black",
        fill=False,
        zorder=10
    )

    ax.add_patch(left_hoop)
    ax.add_patch(right_hoop)

    # THREE POINT LINES
    triple_radius = 6.75

    left_arc = Arc(
        (
            1.575,
            court_width / 2
        ),
        triple_radius * 2,
        triple_radius * 2,
        theta1=-78,
        theta2=78,
        linewidth=2,
        color="black",
        zorder=10
    )

    right_arc = Arc(
        (
            court_length - 1.575,
            court_width / 2
        ),
        triple_radius * 2,
        triple_radius * 2,
        theta1=102,
        theta2=258,
        linewidth=2,
        color="black",
        zorder=10
    )

    ax.add_patch(left_arc)
    ax.add_patch(right_arc)

    # CONFIG
    ax.set_xlim(0, court_length)
    ax.set_ylim(0, court_width)

    ax.set_aspect("equal")

    ax.set_xticks([])
    ax.set_yticks([])


# =========================
# CLEAN DATA
# =========================

def clean_tracking_data(df):

    if df.empty:
        return df

    # REMOVE OUTSIDE COURT
    df = df[
        (df["x"] >= 0) &
        (df["x"] <= 28) &
        (df["y"] >= 0) &
        (df["y"] <= 15)
    ].copy()

    if len(df) < 10:
        return df

    # REMOVE GPS OUTLIERS
    x_min = df["x"].quantile(0.009)
    x_max = df["x"].quantile(0.991)

    y_min = df["y"].quantile(0.009)
    y_max = df["y"].quantile(0.991)

    df = df[
        (df["x"] >= x_min) &
        (df["x"] <= x_max) &
        (df["y"] >= y_min) &
        (df["y"] <= y_max)
    ].copy()

    # AVOID DIVISION BY ZERO
    if df["x"].max() != df["x"].min():

        df["x"] = (
            (
                df["x"] -
                df["x"].min()
            )
            /
            (
                df["x"].max() -
                df["x"].min()
            )
        ) * 28

    if df["y"].max() != df["y"].min():

        df["y"] = (
            (
                df["y"] -
                df["y"].min()
            )
            /
            (
                df["y"].max() -
                df["y"].min()
            )
        ) * 15

    return df


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
# LOAD TRACKING DATA
# =========================

query = """
SELECT
    session_id,
    player_id,
    x,
    y,
    timestamp,
    'COROS' AS source
FROM coros_data
WHERE session_id = ?

UNION ALL

SELECT
    session_id,
    player_id,
    x,
    y,
    timestamp,
    'SUUNTO' AS source
FROM suunto_data
WHERE session_id = ?
"""

tracking_df = pd.read_sql_query(
    query,
    conn,
    params=(session_id, session_id)
)


# =========================
# LOAD PLAYERS
# =========================

player_query = """
SELECT DISTINCT
    p.id,
    p.name,
    p.surname
FROM players p
JOIN (
    SELECT player_id, session_id
    FROM coros_data

    UNION

    SELECT player_id, session_id
    FROM suunto_data
) t
    ON p.id = t.player_id
WHERE t.session_id = ?
ORDER BY p.name
"""

players_df = pd.read_sql_query(
    player_query,
    conn,
    params=(session_id,)
)

conn.close()


# =========================
# VALIDATION
# =========================

if tracking_df.empty:

    st.warning(
        "No hay datos GPS"
    )

    st.stop()


# =========================
# HEATMAPS BY PLAYER
# =========================

for _, player in players_df.iterrows():

    player_id = player["id"]

    player_name = (
        f"{player['name']} {player['surname']}"
    )

    player_tracking = tracking_df[
        tracking_df["player_id"] == player_id
    ].copy()

    if player_tracking.empty:
        continue

    # CLEAN DATA
    player_tracking = clean_tracking_data(
        player_tracking
    )

    if player_tracking.empty:
        continue

    st.divider()

    # SOURCE INFO
    sources = (
        player_tracking["source"]
        .unique()
        .tolist()
    )

    source_text = " + ".join(sources)

    st.subheader(
        f"{player_name}"
    )

    st.caption(
        f"Fuente GPS: {source_text}"
    )

    # =========================
    # TRAINING HEATMAP
    # =========================

    if session_row["flg_game"] == 0:

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        hb = ax.hexbin(
            player_tracking["x"],
            player_tracking["y"],
            gridsize=20,
            extent=(0, 28, 0, 15),
            cmap="Reds",
            mincnt=1
        )

        draw_court(ax)

        cb = fig.colorbar(
            hb,
            ax=ax
        )

        cb.set_label(
            "Densidad"
        )

        st.pyplot(fig)

    # =========================
    # GAME HEATMAPS
    # =========================

    else:

        player_tracking = player_tracking.sort_values(
            by="timestamp"
        )

        mid = len(player_tracking) // 2

        first_half = player_tracking.iloc[:mid]

        second_half = player_tracking.iloc[mid:]

        c1, c2 = st.columns(2)

        # FIRST HALF
        with c1:

            st.markdown(
                "### 1ª Parte"
            )

            fig1, ax1 = plt.subplots(
                figsize=(8, 4)
            )

            hb1 = ax1.hexbin(
                first_half["x"],
                first_half["y"],
                gridsize=20,
                extent=(0, 28, 0, 15),
                cmap="Reds",
                mincnt=1
            )

            draw_court(ax1)

            cb1 = fig1.colorbar(
                hb1,
                ax=ax1
            )

            cb1.set_label(
                "Densidad"
            )

            st.pyplot(fig1)

        # SECOND HALF
        with c2:

            st.markdown(
                "### 2ª Parte"
            )

            fig2, ax2 = plt.subplots(
                figsize=(8, 4)
            )

            hb2 = ax2.hexbin(
                second_half["x"],
                second_half["y"],
                gridsize=20,
                extent=(0, 28, 0, 15),
                cmap="Reds",
                mincnt=1
            )

            draw_court(ax2)

            cb2 = fig2.colorbar(
                hb2,
                ax=ax2
            )

            cb2.set_label(
                "Densidad"
            )

            st.pyplot(fig2)