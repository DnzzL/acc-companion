import streamlit as st

from datetime import timedelta, datetime, date, time
from helpers import *
import pandas as pd

st.sidebar.title("Assetto Corsa Competizione companion app")

tools = ["Fuel calculator", "Endurance Stint Planner"]

tool = st.sidebar.selectbox("Tools", tools)

if tool == tools[0]:
    race_length = st.number_input(f"Race length in minutes", value=0, format="%d")
    fuel_consumption = st.number_input("Fuel consumption in liters", step=0.1)
    pace = st.number_input(f"Average pace in minutes", step=0.1)

    if race_length != 0 and fuel_consumption != 0 and pace != 0:
        race_length_in_seconds = race_length * 60
        pace_in_seconds = decrease_time_unit(pace)
        fuel_with_formation_lap = compute_fuel_to_add(
            race_length_in_seconds, pace_in_seconds, fuel_consumption
        )
        fuel_without_formation_lap = compute_fuel_to_add(
            race_length_in_seconds, pace_in_seconds, fuel_consumption, False
        )
        st.header(
            f"You should add {fuel_with_formation_lap}L with a formation lap \
             or {fuel_without_formation_lap}L without"
        )
        st.write(
            """
            The number of lap is estimated as the length of the stint divided by the average pace, rounded up.
            The fuel to add is the fuel consumption per lap times the number of expected laps + 3% of uncertainty, rounded up.
            An extra lap is added in case of formation lap.
        """
        )

if tool == tools[1]:
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        start_of_race = st.time_input(f"Start of race")
    with col2:
        race_length = st.number_input(f"Length in hours", value=0, format="%d", step=1)
    with col3:
        stint_length = st.number_input(
            f"Stint length in minutes", value=0, format="%d", step=1
        )
    col1, col2 = st.beta_columns(2)
    with col1:
        fuel_consumption = st.number_input("Fuel in liters", step=0.1)
    with col2:
        pit_stop_time_lost = st.number_input(
            "Pit Stop time in seconds", value=50, format="%d", step=1
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
        race_length_in_seconds = race_length * 3600
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
                    (((120 - fuel_consumption) // fuel_consumption) - 1)
                    * drivers[driver]["pace"]
                    - pit_stop_time_lost,
                )
                if stint_number == 0
                else min(
                    max_stint_length_in_seconds - pit_stop_time_lost,
                    ((120 // fuel_consumption) - 1) * drivers[driver]["pace"]
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
        st.table(stints)

        st.write(
            """
            The number of lap is estimated as the length of the stint divided by the average pace, rounded up.
            The fuel to add is the fuel consumption per lap times the number of expected laps + 3% of uncertainty, rounded up.
            An extra lap is added in case of formation lap.
        """
        )
