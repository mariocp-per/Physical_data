import pandas as pd
import numpy as np

# =========================================================
# CONFIG
# =========================================================

SPRINT_SPEED = 5.0           # m/s -> 18 km/h
HSR_SPEED = 4.4              # m/s -> 16 km/h
ACC_THRESHOLD = 2.5          # m/s²
DEC_THRESHOLD = -2.5         # m/s²
MIN_SPRINT_SECONDS = 1

# =========================================================
# PREPARE DATA
# =========================================================


def prepare_dataframe(df):

    if df.empty:
        return df

    df = df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp"]
    )

    df = df.sort_values(
        "timestamp"
    )

    # =====================================================
    # DELTA TIME
    # =====================================================

    df["delta_time"] = (
        df["timestamp"]
        .diff()
        .dt.total_seconds()
    )

    df["delta_time"] = (
        df["delta_time"]
        .fillna(1)
    )

    # =====================================================
    # SPEED
    # =====================================================

    if "speed" in df.columns:

        df["speed"] = (
            pd.to_numeric(
                df["speed"],
                errors="coerce"
            )
            .fillna(0)
        )

        # km/h
        df["speed_kmh"] = (
            df["speed"] * 3.6
        )

    return df

# =========================================================
    return len(rsa_actions)