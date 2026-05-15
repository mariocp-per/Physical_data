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

if sessions_df.empty:

    st.info(
        "La jugadora no tiene sesiones"
    )

    conn.close()

    st.stop()

# =========================
# DATES
# =========================

sessions_df["session_date"] = (
    sessions_df["session_date"]
    .astype(str)
    .str.replace(
        "+00:00",
        "",
        regex=False
    )
)

sessions_df["session_date"] = pd.to_datetime(
    sessions_df["session_date"],
    errors="coerce"
)

sessions_df = sessions_df[
    sessions_df["session_date"].notna()
].copy()

sessions_df = sessions_df.sort_values(
    "session_date",
    ascending=False
)

# =========================
# LABELS
# =========================

sessions_df["label"] = (
    sessions_df["device"]
    + " | Sesión "
    + sessions_df["session_id"]
        .astype(str)
    + " | "
    + sessions_df["session_date"]
        .dt.strftime("%d/%m/%Y %H:%M")
)

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
# HR TIMELINE
# =========================

st.header(
    "Frecuencia cardíaca"
)

session_df["timestamp"] = (
    pd.to_datetime(
        session_df["timestamp"],
        errors="coerce"
    )
)

session_df = session_df.dropna(
    subset=["timestamp"]
)

session_df = session_df.sort_values(
    "timestamp"
)

try:

    session_df["timestamp"] = (
        session_df["timestamp"]
        .dt.tz_localize(None)
    )

except:

    pass

start_time = session_df[
    "timestamp"
].min()

session_df["minutes"] = (
    session_df["timestamp"]
    - start_time
).dt.total_seconds() / 60

# =========================
# HISTORICAL ZONES
# =========================

zone_limits = [
    z1,
    z2,
    z3,
    z4
]

# =========================
# ZONE FUNCTION
# =========================

def get_zone_color(
    hr,
    z1,
    z2,
    z3,
    z4
):

    if hr < z1:

        return "darkgreen"

    elif hr < z2:

        return "blue"

    elif hr < z3:

        return "yellow"

    elif hr < z4:

        return "orange"

    else:

        return "red"

# =========================
# FIGURE
# =========================

fig, ax = plt.subplots(
    figsize=(14, 4)
)

ax.set_facecolor(
    "white"
)

# =========================
# COROS / SUUNTO
# =========================

if selected_device in [
    "COROS",
    "SUUNTO"
]:

    colors = []

    for hr in session_df[
        "heart_rate"
    ]:

        colors.append(
            get_zone_color(
                hr,
                z1,
                z2,
                z3,
                z4
            )
        )

    ax.scatter(
        session_df["minutes"],
        session_df["heart_rate"],
        c=colors,
        s=10,
        alpha=0.9,
        linewidths=0
    )

# =========================
# MYZONE
# =========================

else:

    session_df["minute_bin"] = (
        session_df["minutes"]
        .round()
    )

    myzone_minute = (
        session_df
        .groupby("minute_bin")
        .agg({
            "heart_rate": "mean"
        })
        .reset_index()
    )

    ax.plot(
        myzone_minute["minute_bin"],
        myzone_minute["heart_rate"],
        linewidth=3
    )

# =========================
# AXIS
# =========================

ax.set_xlabel(
    "Minutos"
)

ax.set_ylabel(
    "FC"
)

ax.set_title(
    (
        f"Frecuencia cardíaca - "
        f"{selected_device} - "
        f"Sesión {selected_session_id}"
    )
)

ax.grid(True)

max_minutes = int(
    session_df["minutes"].max()
)

ax.set_xticks(
    range(
        0,
        max_minutes + 5,
        5
    )
)

st.pyplot(fig)

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

        st.header(
            "Velocidad"
        )

        speed_df["speed_kmh"] = (
            speed_df["speed"] * 3.6
        )

        fig_speed, ax_speed = plt.subplots(
            figsize=(14, 4)
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

        st.header(
            "Distancia"
        )

        dist_df["distance_km"] = (
            dist_df["distance"] / 1000
        )

        fig_dist, ax_dist = plt.subplots(
            figsize=(14, 4)
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
    selected_device in [
        "COROS",
        "SUUNTO"
    ]
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

        heatmap_df = heatmap_df[
            (heatmap_df["x"] >= 0)
            &
            (heatmap_df["x"] <= 28)
            &
            (heatmap_df["y"] >= 0)
            &
            (heatmap_df["y"] <= 15)
        ].copy()

        if not heatmap_df.empty:

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

            outer = Rectangle(
                (0, 0),
                28,
                15,
                linewidth=2,
                color="black",
                fill=False
            )

            ax_heat.add_patch(
                outer
            )

            ax_heat.set_xlim(
                0,
                28
            )

            ax_heat.set_ylim(
                0,
                15
            )

            ax_heat.set_aspect(
                "equal"
            )

            ax_heat.set_xticks([])
            ax_heat.set_yticks([])

            cb = fig_heat.colorbar(
                hb,
                ax=ax_heat
            )

            cb.set_label(
                "Densidad"
            )

            st.pyplot(fig_heat)