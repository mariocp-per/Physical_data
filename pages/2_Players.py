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
# METRICS
# =========================

st.header("Métricas")

# PRIORIDAD COROS
if not coros_df.empty:

    summary = build_hr_summary(
        coros_df,
        sample_seconds=1
    )

elif not myzone_df.empty:

    summary = build_hr_summary(
        myzone_df,
        sample_seconds=60
    )

else:

    summary = {}

if summary:

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "FC máxima",
        summary["hr_max"]
    )

    m2.metric(
        "FC media",
        summary["hr_mean"]
    )

    m3.metric(
        "Velocidad máxima",
        summary.get(
            "max_speed",
            None
        )
    )

    m4.metric(
    "Sesiones",
    total_sessions
    )

    st.subheader("Tiempo en zonas")

    zones_df = summary["zones"].copy()

    zone_ranges = summary["zone_ranges"]

    zones_df["bpm_range"] = zones_df[
        "zone"
    ].apply(
        lambda z:
        f"{int(zone_ranges[z][0])}"
        f" - "
        f"{int(zone_ranges[z][1])}"
    )

    zones_df = zones_df[
        [
            "zone",
            "bpm_range",
            "minutes"
        ]
    ]

    zones_df.columns = [
        "Zona",
        "Rango BPM",
        "Minutos"
    ]

    st.dataframe(
        zones_df,
        use_container_width=True
    )

else:

    st.info(
        "No hay datos monitorizados"
    )
# =========================
# HR TIMELINE
# =========================

st.header(
    "Frecuencia cardíaca"
)

conn = get_connection()

# =========================
# LAST 3 SESSIONS
# =========================

sessions_query = """
SELECT DISTINCT
    session_id
FROM coros_data
WHERE player_id = ?

UNION

SELECT DISTINCT
    session_id
FROM myzone_data
WHERE player_id = ?
ORDER BY session_id DESC
LIMIT 3
"""

sessions_df = pd.read_sql_query(
    sessions_query,
    conn,
    params=(
        player_id,
        player_id
    )
)

last_sessions = sessions_df[
    "session_id"
].tolist()

# =========================
# LOAD DATA
# =========================

coros_query = """
SELECT
    timestamp,
    heart_rate,
    session_id
FROM coros_data
WHERE player_id = ?
AND session_id IN ({})
ORDER BY timestamp
""".format(
    ",".join(
        ["?"] * len(last_sessions)
    )
)

coros_params = [
    player_id
] + last_sessions

coros_timeline = pd.read_sql_query(
    coros_query,
    conn,
    params=coros_params
)

myzone_query = """
SELECT
    timestamp,
    heart_rate,
    session_id
FROM myzone_data
WHERE player_id = ?
AND session_id IN ({})
ORDER BY timestamp
""".format(
    ",".join(
        ["?"] * len(last_sessions)
    )
)

myzone_params = [
    player_id
] + last_sessions

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

else:

    timeline_df = myzone_timeline.copy()

    sample_seconds = 60

# =========================
# VALIDATION
# =========================

if timeline_df.empty:

    st.info(
        "No hay datos cardíacos"
    )

else:

    timeline_df["timestamp"] = (
        pd.to_datetime(
            timeline_df["timestamp"]
        )
        .dt.tz_localize(None)
    )

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
    # DRAW SESSION BY SESSION
    # =========================

    for session in last_sessions:

        session_df = timeline_df[
            timeline_df["session_id"] == session
        ].copy()

        if session_df.empty:

            continue

        session_df = session_df.sort_values(
            "timestamp"
        )

        st.subheader(
            f"Sesión {session}"
        )

        # =========================
        # TIME
        # =========================

        start_time = session_df[
            "timestamp"
        ].min()

        session_df["minutes"] = (
            session_df["timestamp"] - start_time
        ).dt.total_seconds() / 60

        # =========================
        # SESSION FC MAX
        # =========================

        hr_max = session_df[
            "heart_rate"
        ].max()

        # =========================
        # ZONES
        # =========================

        z1 = hr_max * 0.60
        z2 = hr_max * 0.70
        z3 = hr_max * 0.80
        z4 = hr_max * 0.90

        zone_limits = [
            z1,
            z2,
            z3,
            z4
        ]

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
        # COROS
        # =========================

        if sample_seconds == 1:

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

            for i in range(
                len(myzone_minute) - 1
            ):

                x1 = myzone_minute.iloc[i][
                    "minute_bin"
                ]

                x2 = myzone_minute.iloc[i + 1][
                    "minute_bin"
                ]

                y1 = myzone_minute.iloc[i][
                    "heart_rate"
                ]

                y2 = myzone_minute.iloc[i + 1][
                    "heart_rate"
                ]

                # =========================
                # FIND CROSSES
                # =========================

                crossings = []

                for limit in zone_limits:

                    if (
                        (y1 < limit and y2 > limit)
                        or
                        (y1 > limit and y2 < limit)
                    ):

                        ratio = (
                            (limit - y1)
                            /
                            (y2 - y1)
                        )

                        cross_x = (
                            x1 +
                            ratio * (x2 - x1)
                        )

                        crossings.append(
                            (
                                cross_x,
                                limit
                            )
                        )

                # =========================
                # BUILD SEGMENTS
                # =========================

                points = [
                    (x1, y1)
                ]

                points.extend(
                    crossings
                )

                points.append(
                    (x2, y2)
                )

                points = sorted(
                    points,
                    key=lambda p: p[0]
                )

                # =========================
                # DRAW SEGMENTS
                # =========================

                for j in range(
                    len(points) - 1
                ):

                    px1, py1 = points[j]

                    px2, py2 = points[j + 1]

                    mid_hr = (
                        py1 + py2
                    ) / 2

                    color = get_zone_color(
                        mid_hr,
                        z1,
                        z2,
                        z3,
                        z4
                    )

                    ax.plot(
                        [px1, px2],
                        [py1, py2],
                        color=color,
                        linewidth=4,
                        solid_capstyle="round"
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
            f"Frecuencia cardíaca - Sesión {session}"
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