import streamlit as st

from datetime import timedelta, datetime, date, time
from helpers import *
import pandas as pd

st.sidebar.title("Assetto Corsa Competizione companion app")

tools = ["Fuel calculator", "Endurance Stint Planner"]

tool = st.sidebar.selectbox("Tools", tools)

if tool == tools[0]:
    st.write("Race Length")
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        race_length_hours = st.number_input(f"hours", key="race-hours", value=0)
    with col2:
        race_length_minutes = st.number_input(f"minutes", key="race-minutes", value=0)
    with col3:
        race_length_seconds = st.number_input(f"seconds", key="race-seconds", value=0)
    st.write("Fuel")
    fuel_tank_size = st.number_input(
        "Fuel tank size in liters", value=0, format="%d", step=1
    )
    fuel_consumption = st.number_input("Fuel consumption in liters", step=0.1)
    st.write("Pace")
    col1, col2 = st.beta_columns(2)
    with col1:
        pace_minutes = st.number_input(f"minutes", key="pace-minutes", value=0)
    with col2:
        pace_seconds = st.number_input(f"seconds", key="pace-seconds", value=0)

    if (
        race_length_hours + race_length_minutes + race_length_seconds > 0
        and fuel_consumption > 0
        and pace_minutes + pace_seconds > 0
    ):
        total_race_length_in_seconds = (
            3600 * race_length_hours + 60 * race_length_minutes + race_length_seconds
        )
        total_pace_pace_in_seconds = 60 * pace_minutes + pace_seconds
        fuel_with_formation_lap = compute_fuel_to_add(
            total_race_length_in_seconds, total_pace_pace_in_seconds, fuel_consumption
        )
        fuel_without_formation_lap = compute_fuel_to_add(
            total_race_length_in_seconds,
            total_pace_pace_in_seconds,
            fuel_consumption,
            False,
        )
        nb_stints = ceil(fuel_with_formation_lap / fuel_tank_size)
        st.write(
            f"You'll need {fuel_with_formation_lap}L to cover {ceil(compute_expected_laps(total_race_length_in_seconds, total_pace_pace_in_seconds))} laps"
        )
        fuel_result = (
            f"You should add {fuel_with_formation_lap}L with a formation lap \
             or {fuel_without_formation_lap}L without"
            if nb_stints == 1
            else f"You should use on average {ceil(fuel_without_formation_lap / nb_stints)}L for each  of your {nb_stints} stints \
            or {nb_stints - 1} stints of {fuel_tank_size}L and {fuel_without_formation_lap % fuel_tank_size}L for the last stint"
        )

        st.header(fuel_result)
        st.text(
            """
            The number of lap is estimated as the length of the stint divided by the average pace, rounded up.
            The fuel to add is the fuel consumption per lap times the number of expected laps + 3% of uncertainty, rounded up.
            An extra lap is added in case of formation lap.
        """
        )

if tool == tools[1]:
    st.write("Race Length")
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        race_length_hours = st.number_input(f"hours", key="race-hours", value=0)
    with col2:
        race_length_minutes = st.number_input(f"minutes", key="race-minutes", value=0)
    with col3:
        race_length_seconds = st.number_input(f"seconds", key="race-seconds", value=0)
    with col1:
        stint_length = st.number_input(
            f"Stint length in minutes", value=0, format="%d", step=1
        )

    col1, col2 = st.beta_columns(2)
    with col1:
        fuel_tank_size = st.number_input(
            "Fuel tank size in liters", value=0, format="%d", step=1
        )
    with col2:
        fuel_consumption = st.number_input(
            "Fuel consumption in liters per lap", step=0.1
        )
    with col1:
        pit_stop_time_lost = st.number_input(
            "Time lost with pit Stop in seconds", value=50, format="%d", step=1
        )
        number_drivers = st.number_input(
            "Number of drivers", value=0, format="%d", step=1
        )
    drivers = {}
    cols = st.beta_columns(max(number_drivers, 1))
    for i in range(number_drivers):
        with cols[i]:
            name = st.text_input(f"Name of driver {i + 1}")
            pace_minutes = st.number_input(f"minutes", key=f"pace-minutes-{i}", value=0)
            pace_seconds = st.number_input(f"seconds", key=f"pace-seconds-{i}")
            drivers[i] = {"name": name, "pace": 60 * pace_minutes + pace_seconds}
    driver_orders = st.text_input("Order of drivers, comma separated (i.e 1,1,2,1,2,2)")
    driver_orders = [int(d) - 1 for d in driver_orders.split(",")]

    total_race_length_in_seconds = (
        3600 * race_length_hours + 60 * race_length_minutes + race_length_seconds
    )
    max_stint_length_in_seconds = decrease_time_unit(stint_length)
    if (
        race_length_hours + race_length_minutes + race_length_seconds > 0
        and fuel_consumption != 0
        and stint_length != 0
        and sum([len(d["name"]) > 0 for i, d in drivers.items()]) == len(drivers)
    ):

        names = []
        fuels = []
        remaining_times = []
        laps = []
        stint_number = 0
        remaining_time = total_race_length_in_seconds
        while remaining_time > 0:
            driver = drivers[driver_orders[stint_number % len(driver_orders)]]
            names.append(driver["name"])
            race_h, race_m, race_s = second_to_hour_minute_second(
                total_race_length_in_seconds
            )
            stint_length_in_seconds = (
                min(
                    max_stint_length_in_seconds - pit_stop_time_lost - driver["pace"],
                    ((fuel_tank_size // fuel_consumption) - 3) * driver["pace"],
                )
                if stint_number == 0
                else min(
                    max_stint_length_in_seconds - pit_stop_time_lost - driver["pace"],
                    ((fuel_tank_size // fuel_consumption) - 2) * driver["pace"],
                )
            )

            remaining_time = (
                total_race_length_in_seconds
                if stint_number == 0
                else remaining_times[stint_number - 1] - stint_length_in_seconds
            )
            remaining_times.append(max(remaining_time, 0))

            if stint_number == 0:
                fuels.append(
                    compute_fuel_to_add(
                        stint_length_in_seconds - pit_stop_time_lost,
                        driver["pace"],
                        fuel_consumption,
                        formation_lap=True,
                    )
                )
            elif remaining_time <= 0:
                fuels.append(0)
            else:
                fuels.append(
                    compute_fuel_to_add(
                        min(
                            stint_length_in_seconds - pit_stop_time_lost,
                            remaining_times[stint_number - 1],
                        ),
                        driver["pace"],
                        fuel_consumption,
                        formation_lap=False,
                    )
                )

            laps.append(
                0
                if stint_number == 0
                else laps[stint_number - 1]
                + compute_expected_laps(stint_length_in_seconds, driver["pace"])
            )
            stint_number += 1

        stints = pd.DataFrame(
            {
                "Name": names,
                "Remaining Time": list(
                    map(second_to_hour_minute_second_string, remaining_times)
                ),
                "Laps": laps,
                "Fuel": fuels,
            }
        )
        st.dataframe(stints)

        st.write(
            """
            The number of lap is estimated as the length of the stint divided by the average pace, rounded up.
            The fuel to add is the fuel consumption per lap times the number of expected laps + 3% of uncertainty, rounded up.
            An extra lap is added in case of formation lap.
        """
        )
