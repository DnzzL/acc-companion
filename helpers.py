from math import ceil


def compute_expected_laps(race_length_in_seconds, pace_in_seconds):
    return race_length_in_seconds // pace_in_seconds + 1


def compute_fuel_to_add(
    race_length_in_seconds, pace_in_seconds, fuel_consumption, formation_lap=True
):
    expected_laps = compute_expected_laps(race_length_in_seconds, pace_in_seconds)
    return ceil(
        1.02 * fuel_consumption * (expected_laps + 1)
        if formation_lap
        else 1.02 * fuel_consumption * expected_laps
    )


def decrease_time_unit(x):
    bigger_unit, smaller_unit = divmod(x, 1)
    if smaller_unit < 10:
        decimals = 100 * smaller_unit
    elif smaller_unit < 100:
        decimals = 1000 * smaller_unit
    else:
        decimals = 10000 * smaller_unit
    return 60 * bigger_unit + decimals


def second_to_hour_minute_second(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return h, m, s


def second_to_hour_minute_second_string(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{str(int(h)).zfill(2)}:{str(int(m)).zfill(2)}:{str(int(s)).zfill(2)}"


def compute_expected_stints(race_length_in_seconds, max_stint_length_in_seconds):
    return ceil(race_length_in_seconds / max_stint_length_in_seconds)