# pages/5_Player_Workload.py

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np

from metrics.session_metrics import (
    build_player_session_metrics
)

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
    SELECT DISTINCT
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
# SAFE METRICS
# =========================================================

def safe_metric(
    metrics,
    key,
    default=0
):

    value = metrics.get(key, default)

    if value is None:
        return default

    return value

# =========================================================
# WORKLOAD FUNCTIONS
# =========================================================

def build_workload_dataframe(player_id):

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
        # SAFE METRICS
        # =================================================

        player_load = safe_metric(
            metrics,
            "player_load"
        )

        sprint_count = safe_metric(
            metrics,
            "sprint_count"
        )

        hsr_distance = safe_metric(
            metrics,
            "hsr_distance"
        )

        total_distance = safe_metric(
            metrics,
            "total_distance"
        )

        sprint_distance = safe_metric(
            metrics,
            "sprint_distance"
        )

        avg_hr = safe_metric(
            metrics,
            "avg_hr"
        )

        max_hr = safe_metric(
            metrics,
            "max_hr"
        )

        max_speed = safe_metric(
            metrics,
            "max_speed"
        )

        accelerations = safe_metric(
            metrics,
            "accelerations"
        )

        decelerations = safe_metric(
            metrics,
            "decelerations"
        )

        # =================================================
        # TRAINING LOAD
        # =================================================

        training_load = (
            player_load * 0.6
            +
            sprint_count * 2
            +
            hsr_distance * 0.05
        )

        # =================================================
        # APPEND
        # =================================================

        data.append({

            "session_id":
                session_id,

            "date":
                row["session_date"],

            "player_load":
                round(player_load, 1),

            "training_load":
                round(training_load, 1),

            "total_distance":
                round(total_distance, 1),

            "hsr_distance":
                round(hsr_distance, 1),

            "sprint_distance":
                round(sprint_distance, 1),

            "sprint_count":
                sprint_count,

            "avg_hr":
                round(avg_hr, 1),

            "max_hr":
                round(max_hr, 1),

            "max_speed":
                round(max_speed, 1),

            "accelerations":
                accelerations,

            "decelerations":
                decelerations
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

    df = df.sort_values(
        "date"
    )

    # =====================================================
    # ACWR
    # =====================================================

    # Acute Load
    df["acute_load"] = (
        df["training_load"]
        .rolling(
            window=7,
            min_periods=1
        )
        .mean()
    )

    # Chronic Load
    df["chronic_load"] = (
        df["training_load"]
        .rolling(
            window=28,
            min_periods=1
        )
        .mean()
    )

    # ACWR
    df["acwr"] = (
        df["acute_load"]
        /
        df["chronic_load"]
    )

    df["acwr"] = (
        df["acwr"]
        .replace(np.inf, np.nan)
        .fillna(0)
    )

    return df

# =========================================================
# IA FUNCTIONS
# =========================================================

def classify_acwr(acwr):

    if acwr == 0:
        return "Sin datos"

    if acwr < 0.8:
        return "Carga baja"

    elif acwr < 1.3:
        return "Óptima"

    elif acwr < 1.5:
        return "Riesgo moderado"

    return "Alto riesgo"


def detect_workload_alerts(latest_row):

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
            "⚠️ Player Load elevado"
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
            "⚠️ HSR distance elevada"
        )

    return alerts


def generate_summary(
    latest_row,
    acwr_label
):

    text = f"""
### Resumen acumulado

La jugadora presenta actualmente
un estado de carga **{acwr_label.lower()}**.

- ACWR actual: **{round(latest_row['acwr'], 2)}**
- Carga aguda: **{round(latest_row['acute_load'], 1)}**
- Carga crónica: **{round(latest_row['chronic_load'], 1)}**
- Player Load último registro: **{latest_row['player_load']}**
- Distancia total: **{latest_row['total_distance']} m**
- HSR Distance: **{latest_row['hsr_distance']} m**
- Número de sprints: **{latest_row['sprint_count']}**
"""

    # =====================================================
    # INTERPRETATION
    # =====================================================

    if latest_row["acwr"] > 1.5:

        text += """

Existe un incremento rápido de carga
respecto al baseline acumulado.

Se recomienda controlar exposición
a alta intensidad.
"""

    elif latest_row["acwr"] < 0.8:

        text += """

Se detecta una posible reducción
del estímulo acumulado.
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
de carga física y ACWR.
""")

# =========================================================
# PLAYERS
# =========================================================

players_df = get_players()

if players_df.empty:

    st.warning(
        "No existen jugadoras"
    )

    st.stop()

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
# BUILD WORKLOAD
# =========================================================

workload_df = build_workload_dataframe(
    selected_player
)

if workload_df.empty:

    st.warning(
        "No existen métricas suficientes"
    )

    st.stop()

# =========================================================
# LATEST ROW
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
# KPIs
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
# LOAD EVOLUTION
# =========================================================

st.subheader("📈 Evolución carga")

load_chart = workload_df[
    [
        "date",
        "training_load",
        "acute_load",
        "chronic_load"
    ]
]

load_chart = load_chart.set_index(
    "date"
)

st.line_chart(load_chart)

# =========================================================
# ACWR EVOLUTION
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

st.subheader("🏃 Distancia Total")

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

st.subheader("💨 Sprint Count")

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

st.subheader("🚀 Evolución futura")

st.markdown("""
Próximos módulos:

- Readiness score
- Wellness
- Fatiga acumulada
- Riesgo lesión
- Comparativa por posición
- Tendencias semanales
- Informes automáticos IA
- Predicción rendimiento
""")