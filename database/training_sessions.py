import pandas as pd

from database.db import get_connection


def create_training_session(
    session_date,
    attendees,
    location,
    flg_game,
    notes=None

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO training_sessions (
        session_date,
        attendees,
        location,
        flg_game,
        notes

    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        session_date,
        attendees,
        location,
        flg_game,
        notes
        
    ))

    conn.commit()

    session_id = cursor.lastrowid

    conn.close()

    return session_id


def get_sessions():

    conn = get_connection()

    query = """
    SELECT *
    FROM training_sessions
    ORDER BY session_date DESC
    """

    df_sessions = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df_sessions


def get_session_by_id(session_id):

    conn = get_connection()

    query = """
    SELECT *
    FROM training_sessions
    WHERE id = ?
    """

    df_session = pd.read_sql_query(
        query,
        conn,
        params=(session_id,)
    )

    conn.close()

    return df_session