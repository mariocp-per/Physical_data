import sqlite3
import pandas as pd

DB_PATH = "BT_db.db"


def get_player_hr_profile(player_id):

    conn = sqlite3.connect(DB_PATH)

    coros_df = pd.read_sql_query(
        f"""
        SELECT heart_rate
        FROM coros_data
        WHERE player_id = {player_id}
        """,
        conn
    )

    myzone_df = pd.read_sql_query(
        f"""
        SELECT heart_rate
        FROM myzone_data
        WHERE player_id = {player_id}
        """,
        conn
    )

    suunto_df = pd.read_sql_query(
        f"""
        SELECT heart_rate
        FROM suunto_data
        WHERE player_id = {player_id}
        """,
        conn
    )

    conn.close()

    all_hr = []

    for df in [
        coros_df,
        myzone_df,
        suunto_df
    ]:

        if not df.empty:

            all_hr.extend(
                df["heart_rate"]
                .dropna()
                .tolist()
            )

    if len(all_hr) == 0:

        return None

    hr_max = max(all_hr)

    zones = {
        "z1": hr_max * 0.60,
        "z2": hr_max * 0.70,
        "z3": hr_max * 0.80,
        "z4": hr_max * 0.90
    }

    return {
        "hr_max": hr_max,
        "zones": zones
    }