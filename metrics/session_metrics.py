# metrics/session_metrics.py

import sqlite3
import pandas as pd

DB_PATH = "BT_db.db"


def build_player_session_metrics(session_id, player_id):

    conn = sqlite3.connect(DB_PATH)

    # =========================================================
    # INFO JUGADORA + SESIÓN
    # =========================================================

    session_query = f"""
    SELECT
        ts.id AS session_id,
        ts.session_date,
        ts.notes,
        ts.location,
        ts.flg_game,

        p.id AS player_id,
        p.name,
        p.surname,
        p.dorsal

    FROM training_sessions ts

    INNER JOIN device_assignments da
        ON da.session_id = ts.id

    INNER JOIN players p
        ON p.id = da.player_id

    WHERE ts.id = {session_id}
    AND p.id = {player_id}
    """

    session_df = pd.read_sql(session_query, conn)

    if session_df.empty:
        conn.close()
        return None

    session_info = session_df.iloc[0]

    # =========================================================
    # COROS DATA
    # =========================================================

    coros_query = f"""
    SELECT
        timestamp,
        heart_rate,
        speed,
        distance,
        x,
        y

    FROM coros_data

    WHERE session_id = {session_id}
    AND player_id = {player_id}

    ORDER BY timestamp
    """

    coros_df = pd.read_sql(coros_query, conn)

    # =========================================================
    # SUUNTO DATA
    # =========================================================

    suunto_query = f"""
    SELECT
        timestamp,
        heart_rate,
        speed,
        distance,
        x,
        y

    FROM suunto_data

    WHERE session_id = {session_id}
    AND player_id = {player_id}

    ORDER BY timestamp
    """

    suunto_df = pd.read_sql(suunto_query, conn)

    # =========================================================
    # MYZONE DATA
    # =========================================================

    myzone_query = f"""
    SELECT
        timestamp,
        heart_rate

    FROM myzone_data

    WHERE session_id = {session_id}
    AND player_id = {player_id}

    ORDER BY timestamp
    """

    myzone_df = pd.read_sql(myzone_query, conn)

    conn.close()

    # =========================================================
    # PRIORIZACIÓN DISPOSITIVOS
    # =========================================================

    # GPS + velocidad
    gps_df = None

    if not coros_df.empty:
        gps_df = coros_df

    elif not suunto_df.empty:
        gps_df = suunto_df

    # FC
    hr_df = None

    if not myzone_df.empty:
        hr_df = myzone_df

    elif not coros_df.empty:
        hr_df = coros_df

    elif not suunto_df.empty:
        hr_df = suunto_df

    # =========================================================
    # MÉTRICAS FC
    # =========================================================

    avg_hr = 0
    max_hr = 0

    if hr_df is not None and not hr_df.empty:

        hr_clean = hr_df["heart_rate"].dropna()

        if not hr_clean.empty:
            avg_hr = round(hr_clean.mean(), 1)
            max_hr = round(hr_clean.max(), 1)

    # =========================================================
    # MÉTRICAS GPS
    # =========================================================

    total_distance = 0
    max_speed = 0
    avg_speed = 0
    sprint_distance = 0
    sprint_count = 0

    if gps_df is not None and not gps_df.empty:

        speed_clean = gps_df["speed"].dropna()
        distance_clean = gps_df["distance"].dropna()

        if not speed_clean.empty:
            max_speed = round(speed_clean.max(), 2)
            avg_speed = round(speed_clean.mean(), 2)

        if not distance_clean.empty:
            total_distance = round(distance_clean.max(), 2)

        # Sprint > 18 km/h
        sprint_df = gps_df[gps_df["speed"] >= 18]

        if not sprint_df.empty:

            sprint_count = len(sprint_df)

            sprint_distance = round(
                sprint_df["distance"].max()
                - sprint_df["distance"].min(),
                2
            )

    # =========================================================
    # ZONAS FC
    # =========================================================

    hr_zones = {
        "z1": 0,
        "z2": 0,
        "z3": 0,
        "z4": 0,
        "z5": 0
    }

    if hr_df is not None and not hr_df.empty:

        for hr in hr_df["heart_rate"].dropna():

            if hr < 120:
                hr_zones["z1"] += 1

            elif hr < 140:
                hr_zones["z2"] += 1

            elif hr < 160:
                hr_zones["z3"] += 1

            elif hr < 180:
                hr_zones["z4"] += 1

            else:
                hr_zones["z5"] += 1

    # =========================================================
    # PLAYER LOAD SIMPLE
    # =========================================================

    player_load = round(
        (
            avg_hr * 0.4
            + total_distance * 0.2
            + max_speed * 2
            + sprint_count * 0.5
        ),
        2
    )

    # =========================================================
    # RESULTADO FINAL
    # =========================================================

    metrics = {

        # Session
        "session_id": session_info["session_id"],
        "session_date": session_info["session_date"],
        "location": session_info["location"],
        "flg_game": session_info["flg_game"],

        # Player
        "player_id": session_info["player_id"],
        "name": session_info["name"],
        "surname": session_info["surname"],
        "dorsal": session_info["dorsal"],

        # HR
        "avg_hr": avg_hr,
        "max_hr": max_hr,

        # GPS
        "total_distance": total_distance,
        "max_speed": max_speed,
        "avg_speed": avg_speed,

        # Sprint
        "sprint_distance": sprint_distance,
        "sprint_count": sprint_count,

        # Zones
        "hr_zones": hr_zones,

        # Load
        "player_load": player_load,

        # Samples
        "gps_samples": 0 if gps_df is None else len(gps_df),
        "hr_samples": 0 if hr_df is None else len(hr_df)
    }

    return metrics