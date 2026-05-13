import fitdecode
import pandas as pd


def load_fit_file(file_path):

    records = []

    with fitdecode.FitReader(file_path) as fit:

        for frame in fit:

            if isinstance(
                frame,
                fitdecode.records.FitDataMessage
            ):

                if frame.name == "record":

                    data = {}

                    for field in frame.fields:

                        data[field.name] = (
                            field.value
                        )

                    records.append(data)

    df = pd.DataFrame(records)

    # =========================
    # COLUMNAS IMPORTANTES
    # =========================

    columns_to_keep = [
        "timestamp",
        "heart_rate",
        "speed",
        "distance",
        "position_lat",
        "position_long"
    ]

    available_columns = [
        col for col in columns_to_keep
        if col in df.columns
    ]

    df_clean = df[
        available_columns
    ].copy()

    # =========================
    # LIMPIEZA
    # =========================

    if "heart_rate" in df_clean.columns:

        df_clean = df_clean.dropna(
            subset=["heart_rate"]
        )

    # =========================
    # TIMESTAMP
    # =========================

    if "timestamp" in df_clean.columns:

        df_clean["timestamp"] = (
            pd.to_datetime(
                df_clean["timestamp"]
            )
        )

        df_clean["timestamp"] = (
            df_clean["timestamp"] +
            pd.Timedelta(hours=2)
        )

    # =========================
    # GPS → X/Y
    # =========================

    if (
        "position_lat" in df_clean.columns
        and
        "position_long" in df_clean.columns
    ):

        SEMICIRCLES_TO_DEGREES = (
            180 / 2**31
        )

        df_clean["lat"] = (
            df_clean["position_lat"] *
            SEMICIRCLES_TO_DEGREES
        )

        df_clean["lon"] = (
            df_clean["position_long"] *
            SEMICIRCLES_TO_DEGREES
        )

        # =========================
        # NORMALIZAR PISTA
        # =========================

        df_clean["x"] = (
            (
                df_clean["lon"] -
                df_clean["lon"].min()
            )
            /
            (
                df_clean["lon"].max() -
                df_clean["lon"].min()
            )
        ) * 28

        df_clean["y"] = (
            (
                df_clean["lat"] -
                df_clean["lat"].min()
            )
            /
            (
                df_clean["lat"].max() -
                df_clean["lat"].min()
            )
        ) * 15

    df_clean = (
        df_clean.reset_index(drop=True)
    )

    return df_clean