# pages/5_Player_Workload.py

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np

# =========================================================
# CONFIG
# =========================================================

DB_PATH = "BT_db.db"

st.set_page_config(
    page_title="Carga Acumulada",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# DB FUNCTIONS
# =========================================================

@st.cache_data
def get_players():

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        id,
        name,
        surname,
        dorsal
    FROM players
    ORDER BY surname
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


@st.cache_data
def get_player_sessions(player_id):

    conn = sqlite3.connect(DB_PATH)

    query = f"""
    SELECT
        ts.id AS session_id,
        ts.session_date,
        ts.location,
        ts.flg_game

    FROM device_assignments da

    INNER JOIN training_sessions ts
        ON ts.id = da.session_id

    WHERE da.player_id = {player_id}

    ORDER BY ts.session_date ASC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df

# =========================================================
# IMPORT METRICS
# =========================================================

from metrics.session_metrics import (
    build_player_session_metrics
)

# =========================================================
# WORKLOAD FUNCTIONS
# =========================================================

def build_workload_dataframe(
    player_id
):

    sessions_df = get_player_sessions(
        player_id
    )

    data = []

    for _, row in sessions_df.iterrows():

        session_id = row["session_id"]

        metrics = build_player_session_metrics(
            session_id,
            player_id
        )

        if metrics is None:
            continue

        # =================================================
        # TRAINING LOAD
        # =================================================

        training_load = (
            metrics["player_load"] * 0.6
            +
            metrics["sprint_count"] * 2
            +
            metrics["hsr_distance"] * 0.05
        )

        data.append({

            "session_id":
                session_id,

            "date":
                row["session_date"],

            "player_load":
                metrics["player_load"],

            "total_distance":
                metrics["total_distance"],

            "hsr_distance":
                metrics["hsr_distance"],

            "sprint_distance":
                metrics["sprint_distance"],

            "sprint_count":
                metrics["sprint_count"],

            "avg_hr":
                metrics["avg_hr"],

            "max_hr":
                metrics["max_hr"],

            "training_load":
                round(training_load, 1)
        })

    df = pd.DataFrame(data)

    if df.empty:
        return df

    # =====================================================
    # DATE
    # =====================================================

    df["date"] = pd.to_datetime(
        df["date"]
    )

    df = df.sort_values("date")

    # =====================================================
    # ACWR
    # =====================================================

    df["acute_load"] = (
        df["training_load"]
        .rolling(7, min_periods=1)
        .mean()
    )

    df["chronic_load"] = (
        df["training_load"]
        .rolling(28, min_periods=1)
        .mean()
    )

    df["acwr"] = (
        df["acute_load"]
        /
        df["chronic_load"]
    )

    df["acwr"] = (
        df["acwr"]
        .replace(np.inf, np.nan)
    )

    return df

# =========================================================
# IA FUNCTIONS
# =========================================================

def classify_acwr(acwr):

    if pd.isna(acwr):
        return "Sin datos"

    if acwr < 0.8:
        return "Baja carga"

    elif acwr < 1.3:
        return "Óptima"

    elif acwr < 1.5:
        return "Riesgo moderado"

    return "Alto riesgo"


def detect_workload_alerts(
    latest_row
):

    alerts = []

    # =====================================================
    # ACWR
    # =====================================================

    if latest_row["acwr"] > 1.5:

        alerts.append(
            "⚠️ ACWR elevado"
        )

    elif latest_row["acwr"] > 1.3:

        alerts.append(
            "⚠️ Incremento rápido de carga"
        )

    # =====================================================
    # PLAYER LOAD
    # =====================================================

    if latest_row["player_load"] > 500:

        alerts.append(
            "⚠️ Player load elevado"
        )

    # =====================================================
    # SPRINTS
    # =====================================================

    if latest_row["sprint_count"] > 25:

        alerts.append(
            "⚠️ Alta exposición sprint"
        )

    # =====================================================
    # HSR
    # =====================================================

    if latest_row["hsr_distance"] > 700:

        alerts.append(
            "⚠️ HSR elevada"
        )

    return alerts


def generate_summary(
    latest_row,
    acwr_label
):

    text = f"""
### Resumen acumulado

La jugadora presenta actualmente un estado
de carga **{acwr_label.lower()}**.

- ACWR actual: **{round(latest_row['acwr'], 2)}**
- Carga aguda (7 sesiones): **{round(latest_row['acute_load'], 1)}**
- Carga crónica (28 sesiones): **{round(latest_row['chronic_load'], 1)}**
- Player Load último registro: **{latest_row['player_load']}**
- Distancia HSR: **{latest_row['hsr_distance']} m**
- Número de sprints: **{latest_row['sprint_count']}**
"""

    # =====================================================
    # ACWR
    # =====================================================

    if latest_row["acwr"] > 1.5:

        text += """

Existe un incremento rápido de carga
respecto al baseline acumulado.
"""

    elif latest_row["acwr"] < 0.8:

        text += """

Se detecta una posible reducción
de estímulo de entrenamiento.
"""

    else:

        text += """

La progresión de carga se encuentra
dentro de parámetros adecuados.
"""

    return text

# =========================================================
# HEADER
# =========================================================

st.title("📈 Carga Acumulada")

st.markdown("""
Monitorización longitudinal
de carga y ACWR.
""")

# =========================================================
# PLAYERS
# =========================================================

players_df = get_players()

selected_player = st.selectbox(
    "Seleccionar jugadora",
    players_df["id"],
    format_func=lambda x:
        (
            f"{players_df[players_df['id'] == x]['surname'].values[0]}, "
            f"{players_df[players_df['id'] == x]['name'].values[0]}"
        )
)

# =========================================================
# BUILD DATA
# =========================================================

workload_df = build_workload_dataframe(
    selected_player
)

if workload_df.empty:

    st.warning(
        "No existen sesiones suficientes"
    )

    st.stop()

# =========================================================
# LATEST
# =========================================================

latest_row = workload_df.iloc[-1]

acwr_label = classify_acwr(
    latest_row["acwr"]
)

alerts = detect_workload_alerts(
    latest_row
)

summary = generate_summary(
    latest_row,
    acwr_label
)

# =========================================================
# TOP KPIs
# =========================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "ACWR",
    round(latest_row["acwr"], 2)
)

c2.metric(
    "Carga Aguda",
    round(latest_row["acute_load"], 1)
)

c3.metric(
    "Carga Crónica",
    round(latest_row["chronic_load"], 1)
)

c4.metric(
    "Estado",
    acwr_label
)

# =========================================================
# ALERTS
# =========================================================

if len(alerts) > 0:

    st.subheader("🚨 Alertas")

    for alert in alerts:

        st.warning(alert)

# =========================================================
# SUMMARY
# =========================================================

st.subheader("🧠 Interpretación")

st.markdown(summary)

# =========================================================
# TRAINING LOAD
# =========================================================

st.subheader("📈 Evolución carga")

chart_df = workload_df[
    [
        "date",
        "training_load",
        "acute_load",
        "chronic_load"
    ]
]

chart_df = chart_df.set_index(
    "date"
)

st.line_chart(chart_df)

# =========================================================
# ACWR
# =========================================================

st.subheader("⚖️ Evolución ACWR")

acwr_chart = workload_df[
    [
        "date",
        "acwr"
    ]
]

acwr_chart = acwr_chart.set_index(
    "date"
)

st.line_chart(acwr_chart)

# =========================================================
# DISTANCE
# =========================================================

st.subheader("🏃 Distancia total")

distance_chart = workload_df[
    [
        "date",
        "total_distance"
    ]
]

distance_chart = distance_chart.set_index(
    "date"
)

st.bar_chart(distance_chart)

# =========================================================
# HSR
# =========================================================

st.subheader("⚡ HSR Distance")

hsr_chart = workload_df[
    [
        "date",
        "hsr_distance"
    ]
]

hsr_chart = hsr_chart.set_index(
    "date"
)

st.line_chart(hsr_chart)

# =========================================================
# SPRINTS
# =========================================================

st.subheader("💨 Sprints")

sprint_chart = workload_df[
    [
        "date",
        "sprint_count"
    ]
]

sprint_chart = sprint_chart.set_index(
    "date"
)

st.bar_chart(sprint_chart)

# =========================================================
# RAW DATA
# =========================================================

with st.expander(
    "Ver datos completos"
):

    st.dataframe(
        workload_df,
        use_container_width=True
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown("""
### 🚀 Próximas evoluciones

- Readiness score
- Fatiga acumulada
- Wellness
- Riesgo lesión
- Predicción rendimiento
- Comparativa por posición
- Tendencias semanales
- Informes automáticos IA
""")