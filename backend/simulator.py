import requests
import random
import time
import math

API_URL = "http://127.0.0.1:8000/api/telemetry"


# ==========================================
# INITIAL CONDITIONS
# ==========================================

temperature = -15.0
altitude = 4500.0

battery_voltage = 12.4
load_voltage = 12.0


# ==========================================
# SIMULATION LOOP
# ==========================================

while True:

    try:

        # ==========================================
        # ALTITUDE
        # ==========================================

        # Slowly vary altitude between 4000 and 6000 m
        altitude += random.uniform(-30, 30)

        altitude = max(
            4000,
            min(6000, altitude)
        )


        # ==========================================
        # ATMOSPHERIC PRESSURE
        # Approximation using barometric formula
        # ==========================================

        pressure = (
            1013.25 *
            (1 - 2.25577e-5 * altitude) ** 5.25588
        )

        pressure += random.uniform(-2, 2)


        # ==========================================
        # AMBIENT TEMPERATURE
        # ==========================================

        # Approximate temperature decrease with altitude
        base_temperature = (
            15 - (0.0065 * altitude)
        )

        temperature += (
            (base_temperature - temperature) * 0.15
        )

        temperature += random.uniform(-0.4, 0.4)


        # ==========================================
        # BATTERY TEMPERATURE
        # ==========================================

        battery_temperature = (
            temperature + 5
            + random.uniform(-0.5, 0.5)
        )


        # ==========================================
        # ELECTRONICS TEMPERATURE
        # Electronics stay slightly warmer
        # because of internal power dissipation
        # ==========================================

        electronics_temperature = (
            temperature + 8
            + random.uniform(-0.5, 0.5)
        )


        # ==========================================
        # BATTERY VOLTAGE
        # Cold conditions cause some voltage sag
        # ==========================================

        cold_factor = max(
            0,
            (-temperature) / 40
        )

        battery_voltage = (
            12.6
            - (cold_factor * 0.45)
            + random.uniform(-0.05, 0.05)
        )


        # ==========================================
        # LOAD CURRENT
        # Cold temperature increases load
        # because of increased mechanical/electrical stress
        # ==========================================

        cold_current_factor = max(
            0,
            (-temperature) * 0.018
        )

        pressure_factor = max(
            0,
            (650 - pressure) * 0.001
        )

        load_current = (
            0.65
            + cold_current_factor
            + pressure_factor
            + random.uniform(-0.04, 0.04)
        )


        # ==========================================
        # BATTERY CURRENT
        # Battery supplies load + overhead
        # ==========================================

        battery_current = (
            load_current * 1.08
            + random.uniform(-0.03, 0.03)
        )


        # ==========================================
        # LOAD VOLTAGE
        # Voltage drops slightly under load
        # ==========================================

        load_voltage = (
            battery_voltage
            - (load_current * 0.15)
            + random.uniform(-0.03, 0.03)
        )


        # ==========================================
        # LIMIT VALUES
        # ==========================================

        battery_voltage = max(
            10.5,
            min(12.8, battery_voltage)
        )

        load_voltage = max(
            10.0,
            min(12.6, load_voltage)
        )

        load_current = max(
            0.1,
            min(2.5, load_current)
        )

        battery_current = max(
            0.1,
            min(3.0, battery_current)
        )


        # ==========================================
        # TELEMETRY PACKET
        # ==========================================

        data = {

            "temperature":
                round(temperature, 2),

            "pressure":
                round(pressure, 2),

            "altitude":
                round(altitude, 2),

            "battery_temperature":
                round(battery_temperature, 2),

            "electronics_temperature":
                round(electronics_temperature, 2),

            "battery_voltage":
                round(battery_voltage, 2),

            "battery_current":
                round(battery_current, 2),

            "load_voltage":
                round(load_voltage, 2),

            "load_current":
                round(load_current, 2)
        }


        # ==========================================
        # SEND TO FASTAPI
        # ==========================================

        response = requests.post(
            API_URL,
            json=data,
            timeout=5
        )


        print(
            "Telemetry sent:",
            response.status_code,
            data
        )


    except requests.exceptions.RequestException as e:

        print(
            "Connection error:",
            e
        )


    except Exception as e:

        print(
            "Simulation error:",
            e
        )


    # ==========================================
    # SEND EVERY 5 SECONDS
    # ==========================================

    time.sleep(5)