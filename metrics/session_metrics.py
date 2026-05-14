# metrics/session_metrics.py

import sqlite3
import pandas as pd

from metrics.player_profile import (
    get_player_hr_profile
)

# =========================================================
# CONFIG
# =========================================================

DB_PATH = "BT_db.db"

# =========================================================
# MAIN FUNCTION
# =========================================================

def build_player_session_metrics(
    session_id,
    player_id
):

    conn = sqlite3.connect(
        DB_PATH
    )

    # =====================================================
    # PLAYER + SESSION INFO
    # =====================================================

    info_query = f"""
    SELECT

        ts.id AS session_id,
        ts.session_date,
        ts.location,
        ts.notes,
        ts.flg_game,

        p.id AS player_id,
        p.name,
        p.surname,
        p.dorsal,
        p.category

    FROM training_sessions ts

    INNER JOIN device_assignments da
        ON da.session_id = ts.id

    INNER JOIN players p
        ON p.id = da.player_id

    WHERE ts.id = {session_id}
    AND p.id = {player_id}
    """

    info_df = pd.read_sql_query(
        info_query,
        conn
    )

    if info_df.empty:

        conn.close()

        return None

    info = info_df.iloc[0]

    # =====================================================
    # COROS
    # =====================================================

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

    coros_df = pd.read_sql_query(
        coros_query,
        conn
    )

    # =====================================================
    # SUUNTO
    # =====================================================

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

    suunto_df = pd.read_sql_query(
        suunto_query,
        conn
    )

    # =====================================================
    # MYZONE
    # =====================================================

    myzone_query = f"""
    SELECT
        timestamp,
        heart_rate

    FROM myzone_data

    WHERE session_id = {session_id}
    AND player_id = {player_id}

    ORDER BY timestamp
    """

    myzone_df = pd.read_sql_query(
        myzone_query,
        conn
    )

    conn.close()

    # =====================================================
    # DEVICE PRIORITY
    # =====================================================

    # GPS / SPEED
    gps_df = None

    if not coros_df.empty:

        gps_df = coros_df

    elif not suunto_df.empty:

        gps_df = suunto_df

    # HEART RATE
    hr_df = None

    if not myzone_df.empty:

        hr_df = myzone_df

    elif not coros_df.empty:

        hr_df = coros_df

    elif not suunto_df.empty:

        hr_df = suunto_df

    # =====================================================
    # HR PROFILE
    # =====================================================

    hr_profile = get_player_hr_profile(
        player_id
    )

    # =====================================================
    # HEART RATE METRICS
    # =====================================================

    avg_hr = 0
    max_hr = 0

    if (
        hr_df is not None
        and
        not hr_df.empty
    ):

        hr_clean = (
            hr_df["heart_rate"]
            .dropna()
        )

        if not hr_clean.empty:

            avg_hr = round(
                hr_clean.mean(),
                1
            )

            max_hr = round(
                hr_clean.max(),
                1
            )

    # =====================================================
    # GPS METRICS
    # =====================================================

    total_distance = 0
    max_speed = 0
    avg_speed = 0

    sprint_distance = 0
    sprint_count = 0

    if (
        gps_df is not None
        and
        not gps_df.empty
    ):

        # SPEED

        if "speed" in gps_df.columns:

            speed_clean = (
                gps_df["speed"]
                .dropna()
            )

            if not speed_clean.empty:

                # m/s -> km/h
                speed_kmh = (
                    speed_clean * 3.6
                )

                max_speed = round(
                    speed_kmh.max(),
                    2
                )

                avg_speed = round(
                    speed_kmh.mean(),
                    2
                )

        # DISTANCE

        if "distance" in gps_df.columns:

            distance_clean = (
                gps_df["distance"]
                .dropna()
            )

            if not distance_clean.empty:

                total_distance = round(
                    distance_clean.max(),
                    2
                )

        # SPRINTS

        if "speed" in gps_df.columns:

            sprint_df = gps_df[
                gps_df["speed"] >= 5
            ].copy()

            if not sprint_df.empty:

                sprint_count = len(
                    sprint_df
                )

                if (
                    "distance"
                    in sprint_df.columns
                ):

                    sprint_distance = round(
                        sprint_df[
                            "distance"
                        ].max()
                        -
                        sprint_df[
                            "distance"
                        ].min(),
                        2
                    )

    # =====================================================
    # HR ZONES
    # =====================================================

    hr_zones = {
        "z1": 0,
        "z2": 0,
        "z3": 0,
        "z4": 0,
        "z5": 0
    }

    if (
        hr_profile is not None
        and
        hr_df is not None
        and
        not hr_df.empty
    ):

        z1 = hr_profile[
            "zones"
        ]["z1"]

        z2 = hr_profile[
            "zones"
        ]["z2"]

        z3 = hr_profile[
            "zones"
        ]["z3"]

        z4 = hr_profile[
            "zones"
        ]["z4"]

        for hr in (
            hr_df["heart_rate"]
            .dropna()
        ):

            if hr < z1:

                hr_zones["z1"] += 1

            elif hr < z2:

                hr_zones["z2"] += 1

            elif hr < z3:

                hr_zones["z3"] += 1

            elif hr < z4:

                hr_zones["z4"] += 1

            else:

                hr_zones["z5"] += 1

    # =====================================================
    # PLAYER LOAD
    # =====================================================

    player_load = round(

        (
            avg_hr * 0.4
            +
            total_distance * 0.02
            +
            max_speed * 2
            +
            sprint_count * 0.5
        ),

        2
    )

    # =====================================================
    # SESSION DURATION
    # =====================================================

    session_duration_minutes = 0

    if (
        gps_df is not None
        and
        not gps_df.empty
        and
        "timestamp" in gps_df.columns
    ):

        gps_df["timestamp"] = pd.to_datetime(
            gps_df["timestamp"],
            errors="coerce"
        )

        gps_df = gps_df.dropna(
            subset=["timestamp"]
        )

        if not gps_df.empty:

            duration = (
                gps_df["timestamp"].max()
                -
                gps_df["timestamp"].min()
            )

            session_duration_minutes = round(
                duration.total_seconds() / 60,
                1
            )

    # =====================================================
    # OUTPUT
    # =====================================================

    metrics = {

        # SESSION
        "session_id":
            info["session_id"],

        "session_date":
            info["session_date"],

        "location":
            info["location"],

        "notes":
            info["notes"],

        "flg_game":
            info["flg_game"],

        # PLAYER
        "player_id":
            info["player_id"],

        "name":
            info["name"],

        "surname":
            info["surname"],

        "dorsal":
            info["dorsal"],

        "category":
            info["category"],

        # HEART RATE
        "avg_hr":
            avg_hr,

        "max_hr":
            max_hr,

        # SPEED
        "max_speed":
            max_speed,

        "avg_speed":
            avg_speed,

        # DISTANCE
        "total_distance":
            total_distance,

        # SPRINT
        "sprint_count":
            sprint_count,

        "sprint_distance":
            sprint_distance,

        # ZONES
        "hr_zones":
            hr_zones,

        # LOAD
        "player_load":
            player_load,

        # DURATION
        "session_duration_minutes":
            session_duration_minutes,

        # SAMPLES
        "gps_samples":
            (
                0
                if gps_df is None
                else len(gps_df)
            ),

        "hr_samples":
            (
                0
                if hr_df is None
                else len(hr_df)
            )
    }

    return metrics