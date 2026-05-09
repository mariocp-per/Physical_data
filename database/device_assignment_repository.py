import pandas as pd

from database.db import get_connection


def assign_device(
    session_id,
    player_id,
    device_type
):

    conn = get_connection()

    cursor = conn.cursor()

    # Evitar duplicados
    cursor.execute("""
    DELETE FROM device_assignments
    WHERE session_id = ?
    AND device_type = ?
    """, (
        session_id,
        device_type
    ))

    cursor.execute("""
    INSERT INTO device_assignments (
        session_id,
        player_id,
        device_type
    )
    VALUES (?, ?, ?)
    """, (
        session_id,
        player_id,
        device_type
    ))

    conn.commit()

    conn.close()


def get_session_assignments(session_id):

    conn = get_connection()

    query = """
    SELECT
        da.id,
        da.device_type,
        p.name,
        p.surname
    FROM device_assignments da
    JOIN players p
        ON da.player_id = p.id
    WHERE da.session_id = ?
    """

    df_assignments = pd.read_sql_query(
        query,
        conn,
        params=(session_id,)
    )

    conn.close()

    return df_assignments


def get_player_id_by_device(
    session_id,
    device_type
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT player_id
    FROM device_assignments
    WHERE session_id = ?
    AND device_type = ?
    """, (
        session_id,
        device_type
    ))

    result = cursor.fetchone()

    conn.close()

    if result is None:
        return None

    return result[0]