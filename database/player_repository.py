import pandas as pd

from database.db import get_connection


def get_players():

    conn = get_connection()

    query = """
    SELECT *
    FROM players
    ORDER BY surname, name
    """

    df_players = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df_players


def get_player_by_id(player_id):

    conn = get_connection()

    query = """
    SELECT *
    FROM players
    WHERE id = ?
    """

    df_player = pd.read_sql_query(
        query,
        conn,
        params=(player_id,)
    )

    conn.close()

    return df_player


def create_player(
    name,
    surname,
    category,
    dorsal
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO players (
        name,
        surname,
        category,
        dorsal
    )
    VALUES (?, ?, ?, ?)
    """, (
        name,
        surname,
        category,
        dorsal
    ))

    conn.commit()

    conn.close()