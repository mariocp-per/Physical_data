from database.db import get_connection


def save_suunto_data(
    df_suunto,
    session_id,
    player_id
):

    conn = get_connection()

    cursor = conn.cursor()

    # =========================
    # BORRAR DATOS PREVIOS
    # =========================

    cursor.execute("""
    DELETE FROM suunto_data
    WHERE session_id = ?
    AND player_id = ?
    """, (
        session_id,
        player_id
    ))

    # =========================
    # INSERTAR NUEVOS DATOS
    # =========================

    for _, row in df_suunto.iterrows():

        cursor.execute("""
        INSERT INTO suunto_data (
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

            str(
                row["timestamp"]
            ),

            row.get(
                "heart_rate",
                None
            ),

            row.get(
                "speed",
                None
            ),

            row.get(
                "distance",
                None
            ),

            row.get(
                "x",
                None
            ),

            row.get(
                "y",
                None
            )
        ))

    conn.commit()

    conn.close()