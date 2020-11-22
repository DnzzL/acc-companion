import streamlit as st

from datetime import timedelta, datetime, date, time
from helpers import *
import pandas as pd

st.sidebar.title("Assetto Corsa Competizione companion app")

tools = ["Fuel calculator", "Endurance Stint Planner"]

tool = st.sidebar.selectbox("Tools", tools)

if tool == tools[0]:
    race_length = st.number_input(f"Race length in minutes", value=0)
    fuel_tank_size = st.number_input(
        "Fuel tank size in liters", value=0, format="%d", step=1
    )
    fuel_consumption = st.number_input("Fuel consumption in liters", step=0.1)
    pace = st.number_input(f"Average pace in minutes", step=0.1)

    if race_length != 0 and fuel_consumption != 0 and pace != 0:
        race_length_in_seconds = decrease_time_unit(race_length)
        pace_in_seconds = decrease_time_unit(pace)
        fuel_with_formation_lap = compute_fuel_to_add(
            race_length_in_seconds, pace_in_seconds, fuel_consumption
        )
        fuel_without_formation_lap = compute_fuel_to_add(
            race_length_in_seconds, pace_in_seconds, fuel_consumption, False
        )
        nb_stints = ceil(fuel_with_formation_lap / fuel_tank_size)
        st.write(
            f"You'll need {fuel_with_formation_lap}L to cover {ceil(compute_expected_laps(race_length_in_seconds, pace_in_seconds))} laps"
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
            The fuel to add is the fuel consumption per lap times the number of expected laps + 2% of uncertainty, rounded up.
            An extra lap is added in case of formation lap.
        """
        )

if tool == tools[1]:
    col1, col2 = st.beta_columns(2)
    with col1:
        race_length = st.number_input(f"Length in hours")
    with col2:
        stint_length = st.number_input(
            f"Stint length in minutes", value=0, format="%d", step=1
        )
    col1, col2, col3 = st.beta_columns(3)
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

    number_drivers = st.number_input("Number of drivers", value=0, format="%d", step=1)
    drivers = {}
    cols = st.beta_columns(max(number_drivers, 1))
    for i in range(number_drivers):
        with cols[i]:
            name = st.text_input(f"Name of driver {i + 1}")
            pace = st.number_input(
                f"Average pace of driver {i + 1} in minutes", step=0.1
            )
            drivers[i] = {"name": name, "pace": decrease_time_unit(pace)}
    drivers_sorted = list(sorted(drivers.keys(), key=lambda x: drivers[x]["pace"]))

    if race_length != 0 and fuel_consumption != 0 and pace != 0 and stint_length != 0:
        race_length_in_seconds = decrease_time_unit(decrease_time_unit(race_length))
        max_stint_length_in_seconds = decrease_time_unit(stint_length)
        names = []
        fuels = []
        remaining_times = []
        laps = []
        stint_number = 0
        remaining_time = race_length_in_seconds
        while remaining_time > 0:
            driver = drivers_sorted[stint_number % len(drivers_sorted)]
            names.append(drivers[driver]["name"])
            race_h, race_m, race_s = second_to_hour_minute_second(
                race_length_in_seconds
            )
            stint_length_in_seconds = (
                min(
                    max_stint_length_in_seconds - pit_stop_time_lost,
                    (((fuel_tank_size - fuel_consumption) // fuel_consumption) - 1)
                    * drivers[driver]["pace"]
                    - pit_stop_time_lost,
                )
                if stint_number == 0
                else min(
                    max_stint_length_in_seconds - pit_stop_time_lost,
                    ((fuel_tank_size // fuel_consumption) - 1) * drivers[driver]["pace"]
                    - pit_stop_time_lost,
                )
            )

            remaining_time = (
                race_length_in_seconds
                if stint_number == 0
                else remaining_times[stint_number - 1] - stint_length_in_seconds
            )
            remaining_times.append(max(remaining_time, 0))

            fuels.append(
                compute_fuel_to_add(
                    stint_length_in_seconds - pit_stop_time_lost,
                    drivers[driver]["pace"],
                    fuel_consumption,
                    formation_lap=True,
                )
                if stint_number == 0
                else compute_fuel_to_add(
                    min(
                        stint_length_in_seconds - pit_stop_time_lost,
                        remaining_times[stint_number - 1],
                    ),
                    drivers[driver]["pace"],
                    fuel_consumption,
                    formation_lap=False,
                )
            )
            laps.append(
                0
                if stint_number == 0
                else laps[stint_number - 1]
                + compute_expected_laps(
                    stint_length_in_seconds, drivers[driver]["pace"]
                )
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
            The fuel to add is the fuel consumption per lap times the number of expected laps + 2% of uncertainty, rounded up.
            An extra lap is added in case of formation lap.
        """
        )
