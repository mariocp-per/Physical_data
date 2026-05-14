# pages/4_IA_Analysis.py

import streamlit as st
import sqlite3
import pandas as pd

from metrics.session_metrics import (
    build_player_session_metrics
)

from metrics.player_profile import (
    get_player_hr_profile
)

# =========================================================
# CONFIG
# =========================================================

DB_PATH = "BT_db.db"

st.set_page_config(
    page_title="IA Rendimiento",
    page_icon="🧠",
    layout="wide"
)

# =========================================================
# DB FUNCTIONS
# =========================================================

@st.cache_data
def get_sessions():

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        id,
        session_date,
        location,
        flg_game,
        notes
    FROM training_sessions
    ORDER BY session_date DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


@st.cache_data
def get_players_by_session(session_id):

    conn = sqlite3.connect(DB_PATH)

    query = f"""
    SELECT DISTINCT
        p.id,
        p.name,
        p.surname,
        p.dorsal

    FROM device_assignments da

    INNER JOIN players p
        ON p.id = da.player_id

    WHERE da.session_id = {session_id}

    ORDER BY p.surname
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df

# =========================================================
# IA FUNCTIONS
# =========================================================

def calcular_intensidad(metrics):

    score = 0

    # FC
    if metrics["avg_hr"] >= 170:
        score += 40

    elif metrics["avg_hr"] >= 155:
        score += 30

    elif metrics["avg_hr"] >= 140:
        score += 20

    else:
        score += 10

    # Distancia
    if metrics["total_distance"] >= 7000:
        score += 30

    elif metrics["total_distance"] >= 5000:
        score += 20

    else:
        score += 10

    # Velocidad
    if metrics["max_speed"] >= 24:
        score += 30

    elif metrics["max_speed"] >= 20:
        score += 20

    else:
        score += 10

    return min(score, 100)


def clasificar_intensidad(score):

    if score >= 80:
        return "Muy alta"

    elif score >= 60:
        return "Alta"

    elif score >= 40:
        return "Moderada"

    return "Baja"


def detectar_fatiga(metrics, hr_profile):

    if hr_profile is None:
        return "Sin datos"

    hr_max = hr_profile["hr_max"]

    hr_ratio = (
        metrics["avg_hr"] / hr_max
    )

    if (
        hr_ratio > 0.85
        and metrics["max_speed"] < 18
    ):
        return "Alta"

    elif hr_ratio > 0.75:
        return "Moderada"

    return "Baja"


def calcular_carga_cardiovascular(metrics):

    zones = metrics["hr_zones"]

    trimp = (
        zones["z1"] * 1
        +
        zones["z2"] * 2
        +
        zones["z3"] * 3
        +
        zones["z4"] * 4
        +
        zones["z5"] * 5
    )

    return round(trimp, 1)


def generar_resumen(
    metrics,
    intensidad,
    fatiga,
    carga_cardio
):

    texto = f"""
### Resumen automático

La sesión de **{metrics['name']} {metrics['surname']}**
presentó una intensidad **{intensidad.lower()}**.

- FC media: **{metrics['avg_hr']} bpm**
- FC máxima: **{metrics['max_hr']} bpm**
- Distancia total: **{metrics['total_distance']} m**
- Velocidad máxima: **{metrics['max_speed']} km/h**
- Número de sprints: **{metrics['sprint_count']}**
- Player Load estimado: **{metrics['player_load']}**
- Carga cardiovascular: **{carga_cardio}**

El análisis detecta un nivel de fatiga
**{fatiga.lower()}**.
"""

    # Intensidad
    if intensidad == "Muy alta":

        texto += """

La jugadora estuvo expuesta a una carga
cardiovascular elevada durante gran parte
de la sesión.
"""

    # Fatiga
    if fatiga == "Alta":

        texto += """

Se detecta posible fatiga neuromuscular
o disminución de rendimiento físico.
"""

    # Sprint
    if metrics["sprint_count"] > 20:

        texto += """

La sesión incluyó un volumen elevado
de acciones de alta intensidad.
"""

    return texto


def generar_recomendacion(
    intensidad,
    fatiga
):

    if (
        intensidad == "Muy alta"
        and fatiga == "Alta"
    ):

        return """
- Recomendada sesión regenerativa
- Controlar carga próximas 48h
- Vigilar recuperación y sueño
- Seguimiento wellness
"""

    elif intensidad in [
        "Alta",
        "Muy alta"
    ]:

        return """
- Monitorizar recuperación
- Controlar hidratación
- Revisar carga semanal acumulada
"""

    elif fatiga == "Moderada":

        return """
- Posible fatiga acumulada
- Vigilar próxima sesión
"""

    return """
- Respuesta fisiológica adecuada
- Recuperación estándar
"""


def generar_alertas(metrics):

    alertas = []

    if metrics["max_hr"] > 190:

        alertas.append(
            "⚠️ FC máxima muy elevada"
        )

    if metrics["max_speed"] > 28:

        alertas.append(
            "⚠️ Pico de velocidad muy alto"
        )

    if metrics["sprint_count"] > 30:

        alertas.append(
            "⚠️ Volumen elevado de sprints"
        )

    if metrics["player_load"] > 500:

        alertas.append(
            "⚠️ Player load elevado"
        )

    return alertas

# =========================================================
# HEADER
# =========================================================

st.title("🧠 IA Rendimiento")

st.markdown("""
Interpretación automática de datos
físicos y fisiológicos.
""")

# =========================================================
# SESSIONS
# =========================================================

sessions_df = get_sessions()

if sessions_df.empty:

    st.warning(
        "No existen sesiones"
    )

    st.stop()

selected_session = st.selectbox(
    "Seleccionar sesión",
    sessions_df["id"],
    format_func=lambda x:
        (
            f"Sesión {x} | "
            f"{sessions_df[sessions_df['id'] == x]['session_date'].values[0]}"
        )
)

# =========================================================
# PLAYERS
# =========================================================

players_df = get_players_by_session(
    selected_session
)

if players_df.empty:

    st.warning(
        "No hay jugadoras asignadas"
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
# BUILD METRICS
# =========================================================

metrics = build_player_session_metrics(
    selected_session,
    selected_player
)

if metrics is None:

    st.error(
        "No hay métricas disponibles"
    )

    st.stop()

# =========================================================
# PLAYER PROFILE
# =========================================================

hr_profile = get_player_hr_profile(
    selected_player
)

# =========================================================
# IA
# =========================================================

intensity_score = calcular_intensidad(
    metrics
)

intensidad = clasificar_intensidad(
    intensity_score
)

fatiga = detectar_fatiga(
    metrics,
    hr_profile
)

carga_cardio = calcular_carga_cardiovascular(
    metrics
)

resumen = generar_resumen(
    metrics,
    intensidad,
    fatiga,
    carga_cardio
)

recomendacion = generar_recomendacion(
    intensidad,
    fatiga
)

alertas = generar_alertas(
    metrics
)

# =========================================================
# TOP METRICS
# =========================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Intensidad",
    intensidad,
    intensity_score
)

c2.metric(
    "Fatiga",
    fatiga
)

c3.metric(
    "Carga cardio",
    carga_cardio
)

c4.metric(
    "Player Load",
    metrics["player_load"]
)

# =========================================================
# ALERTS
# =========================================================

if len(alertas) > 0:

    st.subheader("🚨 Alertas")

    for alerta in alertas:

        st.warning(alerta)

# =========================================================
# SUMMARY
# =========================================================

st.subheader("📋 Resumen IA")

st.markdown(resumen)

# =========================================================
# RECOMMENDATION
# =========================================================

st.subheader("✅ Recomendación")

st.success(recomendacion)

# =========================================================
# HR ZONES
# =========================================================

st.subheader("❤️ Zonas FC")

zones_df = pd.DataFrame({

    "Zona": list(
        metrics["hr_zones"].keys()
    ),

    "Tiempo": list(
        metrics["hr_zones"].values()
    )
})

st.bar_chart(
    zones_df.set_index("Zona")
)

# =========================================================
# RAW DATA
# =========================================================

with st.expander(
    "Ver métricas completas"
):

    st.json(metrics)

# =========================================================
# FUTURE
# =========================================================

st.divider()

st.subheader(
    "🚀 Evolución futura"
)

st.markdown("""
Próximos módulos IA:

- Riesgo lesión
- ACWR
- Readiness score
- Comparativa por posición
- Fatiga acumulada
- Análisis táctico
- Heatmaps inteligentes
- Predicción de rendimiento
- IA conversacional para staff técnico
""")