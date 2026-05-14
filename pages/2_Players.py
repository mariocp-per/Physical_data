# pages/2_Players.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.patches import (
    Rectangle,
    Circle,
    Arc
)

from database.player_repository import (
    get_players
)

from database.db import (
    get_connection
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

if historical_hr_max is not None:

    st.subheader(
        "Tiempo en zonas"
    )

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

st.header(
    "Sesión"
)

sessions_query = f"""
SELECT *
FROM (

    SELECT
        da.session_id as session_id,
        da.device_type as device,
        MAX(c.timestamp) as session_date
    FROM device_assignments da
    LEFT JOIN coros_data c
        ON da.session_id = c.session_id
        AND da.player_id = c.player_id
    WHERE da.player_id = {player_id}
    AND da.device_type = 'COROS'
    GROUP BY
        da.session_id,
        da.device_type

    UNION ALL

    SELECT
        da.session_id as session_id,
        da.device_type as device,
        MAX(m.timestamp) as session_date
    FROM device_assignments da
    LEFT JOIN myzone_data m
        ON da.session_id = m.session_id
        AND da.player_id = m.player_id
    WHERE da.player_id = {player_id}
    AND da.device_type = 'MYZONE'
    GROUP BY
        da.session_id,
        da.device_type

    UNION ALL

    SELECT
        da.session_id as session_id,
        da.device_type as device,
        MAX(s.timestamp) as session_date
    FROM device_assignments da
    LEFT JOIN suunto_data s
        ON da.session_id = s.session_id
        AND da.player_id = s.player_id
    WHERE da.player_id = {player_id}
    AND da.device_type = 'SUUNTO'
    GROUP BY
        da.session_id,
        da.device_type

)

ORDER BY session_date DESC
"""

sessions_df = pd.read_sql_query(
    sessions_query,
    conn
)

# =========================
# VALIDATION
# =========================

if sessions_df.empty:

    st.info(
        "La jugadora no tiene sesiones"
    )

    conn.close()

    st.stop()

# =========================
# CLEAN DATES
# =========================

sessions_df["session_date"] = pd.to_datetime(
    sessions_df["session_date"],
    errors="coerce"
)

valid_dates = sessions_df[
    sessions_df["session_date"].notna()
].copy()

invalid_dates = sessions_df[
    sessions_df["session_date"].isna()
].copy()

valid_dates = valid_dates.sort_values(
    "session_date",
    ascending=False
)

sessions_df = pd.concat(
    [
        valid_dates,
        invalid_dates
    ]
)

sessions_df["session_date"] = (
    sessions_df["session_date"]
    .astype(str)
    .replace("NaT", "Sin fecha")
)

# =========================
# CLEAN LABEL FIELDS
# =========================

sessions_df["device"] = (
    sessions_df["device"]
    .fillna("UNKNOWN")
    .astype(str)
)

sessions_df["session_id"] = (
    sessions_df["session_id"]
    .fillna(-1)
    .astype(int)
)

sessions_df["session_date"] = (
    sessions_df["session_date"]
    .fillna("Sin fecha")
    .astype(str)
)

# =========================
# LABELS
# =========================

sessions_df["label"] = (
    sessions_df["device"]
    + " | Sesión "
    + sessions_df["session_id"].astype(str)
    + " | "
    + sessions_df["session_date"]
)

# =========================
# REMOVE INVALID LABELS
# =========================

sessions_df = sessions_df[
    sessions_df["label"].notna()
]

sessions_df = sessions_df[
    sessions_df["session_id"] != -1
]
# =========================
# SESSION OPTIONS
# =========================

session_options = {
    row["label"]: {
        "session_id": row["session_id"],
        "device": row["device"]
    }
    for _, row in sessions_df.iterrows()
}

selected_label = st.selectbox(
    "Seleccionar sesión",
    list(session_options.keys()),
    index=0
)

selected_session = session_options[
    selected_label
]

selected_session_id = (
    selected_session["session_id"]
)

selected_device = (
    selected_session["device"]
)

# =========================
# LOAD SESSION DATA
# =========================

if selected_device == "COROS":

    session_query = f"""
    SELECT *
    FROM coros_data
    WHERE player_id = {player_id}
    AND session_id = {selected_session_id}
    ORDER BY timestamp
    """

elif selected_device == "MYZONE":

    session_query = f"""
    SELECT *
    FROM myzone_data
    WHERE player_id = {player_id}
    AND session_id = {selected_session_id}
    ORDER BY timestamp
    """

else:

    session_query = f"""
    SELECT *
    FROM suunto_data
    WHERE player_id = {player_id}
    AND session_id = {selected_session_id}
    ORDER BY timestamp
    """

session_df = pd.read_sql_query(
    session_query,
    conn
)

# =========================
# LOAD TRAINING SESSION
# =========================

training_query = f"""
SELECT *
FROM training_sessions
WHERE id = {selected_session_id}
"""

training_df = pd.read_sql_query(
    training_query,
    conn
)

conn.close()

# =========================
# VALIDATION
# =========================

if session_df.empty:

    st.warning(
        "No hay datos para la sesión"
    )

    st.stop()

# =========================
# CLEAN TIMESTAMP
# =========================

session_df["timestamp"] = pd.to_datetime(
    session_df["timestamp"],
    errors="coerce"
)

session_df = session_df.dropna(
    subset=["timestamp"]
)

session_df = session_df.sort_values(
    "timestamp"
)

# =========================
# TIME AXIS
# =========================

start_time = session_df[
    "timestamp"
].min()

session_df["minutes"] = (
    session_df["timestamp"]
    - start_time
).dt.total_seconds() / 60

# =========================
# HR GRAPH
# =========================

st.subheader(
    "Frecuencia cardíaca"
)

fig_hr, ax_hr = plt.subplots(
    figsize=(14, 5)
)

ax_hr.plot(
    session_df["minutes"],
    session_df["heart_rate"],
    linewidth=2
)

ax_hr.set_xlabel(
    "Minutos"
)

ax_hr.set_ylabel(
    "FC"
)

ax_hr.grid(True)

st.pyplot(fig_hr)

# =========================
# SPEED GRAPH
# =========================

if (
    "speed" in session_df.columns
):

    speed_df = session_df.dropna(
        subset=["speed"]
    ).copy()

    if not speed_df.empty:

        st.subheader(
            "Velocidad"
        )

        speed_df["speed_kmh"] = (
            speed_df["speed"] * 3.6
        )

        fig_speed, ax_speed = plt.subplots(
            figsize=(14, 5)
        )

        ax_speed.plot(
            speed_df["minutes"],
            speed_df["speed_kmh"],
            linewidth=2
        )

        ax_speed.set_xlabel(
            "Minutos"
        )

        ax_speed.set_ylabel(
            "km/h"
        )

        ax_speed.grid(True)

        st.pyplot(fig_speed)

# =========================
# DISTANCE GRAPH
# =========================

if (
    "distance" in session_df.columns
):

    dist_df = session_df.dropna(
        subset=["distance"]
    ).copy()

    if not dist_df.empty:

        st.subheader(
            "Distancia acumulada"
        )

        dist_df["distance_km"] = (
            dist_df["distance"] / 1000
        )

        fig_dist, ax_dist = plt.subplots(
            figsize=(14, 5)
        )

        ax_dist.plot(
            dist_df["minutes"],
            dist_df["distance_km"],
            linewidth=2
        )

        ax_dist.set_xlabel(
            "Minutos"
        )

        ax_dist.set_ylabel(
            "Kilómetros"
        )

        ax_dist.grid(True)

        st.pyplot(fig_dist)

# =========================
# HEATMAP
# =========================

if (
    selected_device in ["COROS", "SUUNTO"]
    and "x" in session_df.columns
    and "y" in session_df.columns
):

    heatmap_df = session_df.dropna(
        subset=["x", "y"]
    ).copy()

    if not heatmap_df.empty:

        st.header(
            "🔥 Heatmap"
        )

        # REMOVE OUTSIDE COURT

        heatmap_df = heatmap_df[
            (heatmap_df["x"] >= 0)
            &
            (heatmap_df["x"] <= 28)
            &
            (heatmap_df["y"] >= 0)
            &
            (heatmap_df["y"] <= 15)
        ].copy()

        # REMOVE OUTLIERS

        x_min = heatmap_df["x"].quantile(0.009)
        x_max = heatmap_df["x"].quantile(0.991)

        y_min = heatmap_df["y"].quantile(0.009)
        y_max = heatmap_df["y"].quantile(0.991)

        heatmap_df = heatmap_df[
            (heatmap_df["x"] >= x_min)
            &
            (heatmap_df["x"] <= x_max)
            &
            (heatmap_df["y"] >= y_min)
            &
            (heatmap_df["y"] <= y_max)
        ].copy()

        # RESCALE

        heatmap_df["x"] = (
            (
                heatmap_df["x"]
                - heatmap_df["x"].min()
            )
            /
            (
                heatmap_df["x"].max()
                - heatmap_df["x"].min()
            )
        ) * 28

        heatmap_df["y"] = (
            (
                heatmap_df["y"]
                - heatmap_df["y"].min()
            )
            /
            (
                heatmap_df["y"].max()
                - heatmap_df["y"].min()
            )
        ) * 15

        # COURT

        def draw_court(ax):

            court_length = 28
            court_width = 15

            outer = Rectangle(
                (0, 0),
                court_length,
                court_width,
                linewidth=2,
                color="black",
                fill=False
            )

            ax.add_patch(outer)

            ax.plot(
                [court_length / 2,
                 court_length / 2],
                [0, court_width],
                color="black"
            )

            center_circle = Circle(
                (
                    court_length / 2,
                    court_width / 2
                ),
                1.8,
                linewidth=2,
                color="black",
                fill=False
            )

            ax.add_patch(center_circle)

            ax.set_xlim(0, 28)
            ax.set_ylim(0, 15)

            ax.set_aspect("equal")

            ax.set_xticks([])
            ax.set_yticks([])

        # DRAW HEATMAP

        fig_heat, ax_heat = plt.subplots(
            figsize=(10, 5)
        )

        hb = ax_heat.hexbin(
            heatmap_df["x"],
            heatmap_df["y"],
            gridsize=20,
            extent=(0, 28, 0, 15),
            cmap="Reds",
            mincnt=1
        )

        draw_court(ax_heat)

        cb = fig_heat.colorbar(
            hb,
            ax=ax_heat
        )

        cb.set_label(
            "Densidad"
        )

        st.pyplot(fig_heat)