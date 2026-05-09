from database.db import get_connection


def save_myzone_data(
    df_myzone,
    session_id,
    player_id
):

    conn = get_connection()

    cursor = conn.cursor()

    # =========================
    # BORRAR DATOS PREVIOS
    # =========================

    cursor.execute("""
    DELETE FROM myzone_data
    WHERE session_id = ?
    AND player_id = ?
    """, (
        session_id,
        player_id
    ))


    # =========================
    # ELIMINAR DATOS PREVIOS
    # =========================

    cursor.execute("""
    DELETE FROM myzone_data
    WHERE session_id = ?
    AND player_id = ?
    """, (
        session_id,
        player_id
    ))

    # =========================
    # INSERTAR NUEVOS DATOS
    # =========================

    for _, row in df_myzone.iterrows():

        cursor.execute("""
        INSERT INTO myzone_data (
            session_id,
            player_id,
            timestamp,
            heart_rate
        )
        VALUES (?, ?, ?, ?)
        """, (
            session_id,
            player_id,
            str(row["timestamp"]),
            row["heart_rate"]
        ))

    conn.commit()

    conn.close()