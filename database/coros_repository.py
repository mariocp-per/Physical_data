from database.db import get_connection


def save_coros_data(
    df_coros,
    session_id,
    player_id
):

    conn = get_connection()

    cursor = conn.cursor()

    # =========================
    # BORRAR DATOS PREVIOS
    # =========================

    cursor.execute("""
    DELETE FROM coros_data
    WHERE session_id = ?
    AND player_id = ?
    """, (
        session_id,
        player_id
    ))

    # =========================
    # INSERTAR NUEVOS DATOS
    # =========================

    cursor.execute("""
    DELETE FROM coros_data
    WHERE session_id = ?
    AND player_id = ?
    """, (
        session_id,
        player_id
))

    for _, row in df_coros.iterrows():

        cursor.execute("""
        INSERT INTO coros_data (
            session_id,
            player_id,
            timestamp,
            heart_rate,
            speed,
            distance,
            x,
            y
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            player_id,
            str(row["timestamp"]),
            row["heart_rate"],
            row["speed"],
            row["distance"],
            row["x"],
            row["y"]
        ))

    conn.commit()

    conn.close()