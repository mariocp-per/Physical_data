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
# LOAD COROS DATA
# =========================

query = """
SELECT *
FROM coros_data
WHERE session_id = ?
"""

coros_df = pd.read_sql_query(
    query,
    conn,
    params=(session_id,)
)

# =========================
# LOAD PLAYER
# =========================

player_query = """
SELECT DISTINCT
    p.name,
    p.surname
FROM coros_data cd
JOIN players p
    ON cd.player_id = p.id
WHERE cd.session_id = ?
"""

player_df = pd.read_sql_query(
    player_query,
    conn,
    params=(session_id,)
)

conn.close()

if not player_df.empty:

    player_name = (
        player_df.iloc[0]["name"]
        + " "
        + player_df.iloc[0]["surname"]
    )

else:

    player_name = "Desconocida"


# =========================
# VALIDATION
# =========================

if coros_df.empty:

    st.warning(
        "No hay datos COROS"
    )

    st.stop()


# =========================
# REMOVE OUTSIDE COURT
# =========================

coros_df = coros_df[
    (coros_df["x"] >= 0) &
    (coros_df["x"] <= 28) &
    (coros_df["y"] >= 0) &
    (coros_df["y"] <= 15)
].copy()


# =========================
# REMOVE GPS OUTLIERS
# =========================

x_min = coros_df["x"].quantile(0.009)
x_max = coros_df["x"].quantile(0.991)

y_min = coros_df["y"].quantile(0.009)
y_max = coros_df["y"].quantile(0.991)

coros_df = coros_df[
    (coros_df["x"] >= x_min) &
    (coros_df["x"] <= x_max) &
    (coros_df["y"] >= y_min) &
    (coros_df["y"] <= y_max)
].copy()


# =========================
# RESCALE TO FULL COURT
# =========================

coros_df["x"] = (
    (
        coros_df["x"] -
        coros_df["x"].min()
    )
    /
    (
        coros_df["x"].max() -
        coros_df["x"].min()
    )
) * 28

coros_df["y"] = (
    (
        coros_df["y"] -
        coros_df["y"].min()
    )
    /
    (
        coros_df["y"].max() -
        coros_df["y"].min()
    )
) * 15


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
# TRAINING HEATMAP
# =========================

if session_row["flg_game"] == 0:

    st.subheader(
        f"Heatmap entrenamiento - {player_name}"
    )

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    hb = ax.hexbin(
        coros_df["x"],
        coros_df["y"],
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

    st.subheader(
        f"Partido - {player_name}"
    )

    mid = len(coros_df) // 2

    first_half = coros_df.iloc[:mid]

    second_half = coros_df.iloc[mid:]

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

        fig1.colorbar(
            hb1,
            ax=ax1
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

        fig2.colorbar(
            hb2,
            ax=ax2
        )

        st.pyplot(fig2)