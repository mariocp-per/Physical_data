import pandas as pd


# =========================
# HEART RATE MAX
# =========================

def get_hr_peak(df):

    if df.empty:
        return None

    if "heart_rate" not in df.columns:
        return None

    return round(
        df["heart_rate"].max(),
        1
    )

def get_hr_max(
    df,
    quantile=0.995
):

    if df.empty:
        return None

    if "heart_rate" not in df.columns:
        return None

    return round(
        df["heart_rate"].quantile(
            quantile
        ),
        1
    )


# =========================
# HEART RATE MEAN
# =========================

def get_hr_mean(df):

    if df.empty:
        return None

    return round(
        df["heart_rate"].mean(),
        1
    )


# =========================
# HEART RATE ZONES
# =========================

def get_hr_zone(
    hr,
    hr_max
):

    if pd.isna(hr):
        return None

    percentage = (
        hr / hr_max
    ) * 100

    if percentage < 60:
        return "Z1"

    elif percentage < 70:
        return "Z2"

    elif percentage < 80:
        return "Z3"

    elif percentage < 90:
        return "Z4"

    else:
        return "Z5"


# =========================
# ADD HR ZONES
# =========================

def add_hr_zones(
    df,
    hr_max
):

    if df.empty:
        return df

    df = df.copy()

    df["hr_zone"] = df[
        "heart_rate"
    ].apply(
        lambda x: get_hr_zone(
            x,
            hr_max
        )
    )

    return df


# =========================
# TIME IN ZONES
# =========================

def get_time_in_zones(
    df,
    sample_seconds=1
):

    if df.empty:
        return pd.DataFrame()

    if "hr_zone" not in df.columns:
        return pd.DataFrame()

    zone_counts = (
        df["hr_zone"]
        .value_counts()
        .sort_index()
    )

    df_zones = zone_counts.reset_index()

    df_zones.columns = [
        "zone",
        "samples"
    ]

    df_zones["seconds"] = (
        df_zones["samples"] *
        sample_seconds
    )

    df_zones["minutes"] = round(
        df_zones["seconds"] / 60,
        1
    )

    return df_zones


# =========================
# ZONES
# =========================


def get_zone_ranges(hr_peak):

    return {
        "Z1": (
            round(hr_peak * 0.50, 0),
            round(hr_peak * 0.60, 0)
        ),
        "Z2": (
            round(hr_peak * 0.60, 0),
            round(hr_peak * 0.70, 0)
        ),
        "Z3": (
            round(hr_peak * 0.70, 0),
            round(hr_peak * 0.80, 0)
        ),
        "Z4": (
            round(hr_peak * 0.80, 0),
            round(hr_peak * 0.90, 0)
        ),
        "Z5": (
            round(hr_peak * 0.90, 0),
            round(hr_peak * 1.00, 0)
        )
    }



# =========================
# MAX SPEED
# =========================




def get_max_speed(df):

    if df.empty:
        return None

    if "speed" not in df.columns:
        return None

    return round(
        df["speed"].max(),
        2
    )


# =========================
# SESSION SUMMARY
# =========================

def build_hr_summary(
    df,
    sample_seconds=1
):

    if df.empty:
        return {}

    hr_peak = get_hr_peak(df)

    df = add_hr_zones(
        df,
        hr_peak
    )

    hr_max = get_hr_max(df)

    hr_mean = get_hr_mean(df)


    zones = get_time_in_zones(
    df,
    sample_seconds
    )

    zone_ranges = get_zone_ranges(
    hr_peak
    )

    max_speed = get_max_speed(df)

    return {
        "hr_max": hr_max,
        "hr_mean": hr_mean,
        "max_speed": max_speed,
        "zone_ranges": zone_ranges,
        "zones": zones,
        "data": df,
        "hr_peak": hr_peak
    }

