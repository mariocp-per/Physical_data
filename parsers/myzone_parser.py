import pandas as pd
from io import StringIO


def parse_myzone_summary(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    headers = lines[0].strip().split(",")
    values = lines[1].strip().split(",")

    summary = dict(
        zip(headers, values)
    )

    return summary


def parse_myzone_timeline(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # =========================
    # BUSCAR TIMELINE
    # =========================

    start_idx = None

    for i, line in enumerate(lines):

        if line.strip().startswith(
            "Tiempo,hr"
        ):
            start_idx = i
            break

    if start_idx is None:

        raise ValueError(
            "No se encontró timeline"
        )

    # =========================
    # CONSTRUIR CSV TEMPORAL
    # =========================

    timeline_text = "".join(
        lines[start_idx:]
    )

    df_timeline = pd.read_csv(
        StringIO(timeline_text)
    )

    # =========================
    # RENOMBRAR COLUMNAS
    # =========================

    df_timeline.columns = [
        "timestamp",
        "heart_rate"
    ]

    # =========================
    # LIMPIEZA
    # =========================

    df_timeline["timestamp"] = (
        pd.to_datetime(
            df_timeline["timestamp"]
        )
    )

    df_timeline["heart_rate"] = (
        pd.to_numeric(
            df_timeline["heart_rate"],
            errors="coerce"
        )
    )

    df_timeline = (
        df_timeline.dropna()
    )

    df_timeline = (
        df_timeline.reset_index(drop=True)
    )

    return df_timeline