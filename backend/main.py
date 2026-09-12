from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

import os


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL or SUPABASE_KEY is missing in .env"
    )


# ==========================================
# SUPABASE CONNECTION
# ==========================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="SIH #49 Telemetry Backend",
    description="Telemetry monitoring system for High Altitude Areas",
    version="1.0.0"
)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# TELEMETRY DATA MODEL
# ==========================================

class Telemetry(BaseModel):

    temperature: float
    pressure: float
    altitude: float

    battery_temperature: float
    electronics_temperature: float

    battery_voltage: float
    battery_current: float

    load_voltage: float
    load_current: float


# ==========================================
# RELIABILITY / HEALTH MODEL
# ==========================================

def calculate_reliability(data):
    """
    Calculate derived equipment parameters
    from environmental and electrical telemetry.
    """

    temperature = float(
        data.get("temperature", -15)
    )

    pressure = float(
        data.get("pressure", 650)
    )

    load_current = float(
        data.get("load_current", 0.5)
    )

    electronics_temperature = float(
        data.get(
            "electronics_temperature",
            temperature + 8
        )
    )


    # ==========================================
    # RPM MODEL
    # ==========================================

    nominal_rpm = 2300

    # Cold temperature increases mechanical resistance
    cold_stress = max(
        0,
        -temperature
    )

    # Lower pressure represents higher altitude
    pressure_difference = max(
        0,
        650 - pressure
    )

    rpm_loss_temperature = (
        cold_stress * 2.0
    )

    rpm_loss_pressure = (
        pressure_difference * 0.15
    )

    rpm = (
        nominal_rpm
        - rpm_loss_temperature
        - rpm_loss_pressure
    )

    # No random variation.
    # Same telemetry gives same RPM.

    rpm = round(rpm)

    rpm = max(
        0,
        rpm
    )


    # ==========================================
    # RPM STABILITY
    # ==========================================

    rpm_deviation = abs(
        nominal_rpm - rpm
    )

    rpm_stability = max(
        0,
        100 -
        (
            rpm_deviation
            / nominal_rpm
            * 100
        )
    )


    # ==========================================
    # TEMPERATURE STRESS
    # ==========================================

    temperature_stress = min(
        100,
        max(
            0,
            (abs(temperature) - 5) * 1.8
        )
    )


    # ==========================================
    # PRESSURE STRESS
    # ==========================================

    pressure_stress_score = min(
        100,
        max(
            0,
            (650 - pressure) * 0.20
        )
    )


    # ==========================================
    # CURRENT STRESS
    # ==========================================

    current_stress = min(
        100,
        max(
            0,
            (load_current - 0.8) * 80
        )
    )


    # ==========================================
    # ELECTRONICS THERMAL STRESS
    # ==========================================

    electronics_stress = min(
        100,
        max(
            0,
            (electronics_temperature + 5) * 2
        )
    )


    # ==========================================
    # HEALTH SCORE
    # ==========================================

    health = (
        100
        - (temperature_stress * 0.30)
        - (pressure_stress_score * 0.15)
        - (current_stress * 0.20)
        - ((100 - rpm_stability) * 0.25)
        - (electronics_stress * 0.10)
    )

    health = round(
        max(
            0,
            min(
                100,
                health
            )
        )
    )


    # ==========================================
    # ALERT LEVEL
    # ==========================================

    if health >= 85:

        alert_level = "NORMAL"

    elif health >= 65:

        alert_level = "WARNING"

    else:

        alert_level = "CRITICAL"


    # ==========================================
    # ALERT MESSAGE
    # ==========================================

    if health < 65:

        alert_message = (
            "CRITICAL: Equipment health degraded. "
            "Immediate inspection recommended."
        )

    elif load_current > 1.5:

        alert_message = (
            "WARNING: High load current detected. "
            "Possible cold-condition mechanical resistance."
        )

    elif temperature < -30:

        alert_message = (
            "WARNING: Extreme low temperature detected. "
            "Thermal stress elevated."
        )

    elif pressure < 500:

        alert_message = (
            "WARNING: Very low atmospheric pressure detected. "
            "Thermal dissipation capability reduced."
        )

    elif health < 85:

        alert_message = (
            "WARNING: Equipment operating under elevated "
            "environmental or electrical stress."
        )

    else:

        alert_message = (
            "NORMAL: Equipment operating within "
            "acceptable environmental limits."
        )


    # ==========================================
    # RETURN RELIABILITY DATA
    # ==========================================

    return {

        "rpm":
            round(rpm),

        "rpm_stability":
            round(rpm_stability, 1),

        "temperature_stress":
            round(temperature_stress, 1),

        "pressure_stress":
            round(pressure_stress_score, 1),

        "current_stress":
            round(current_stress, 1),

        "electronics_stress":
            round(electronics_stress, 1),

        "health":
            health,

        "alert_level":
            alert_level,

        "alert_message":
            alert_message
    }


# ==========================================
# HOME ENDPOINT
# ==========================================

@app.get("/")
def home():

    return {
        "message": "SIH #49 Backend is running"
    }


# ==========================================
# GET TELEMETRY
# ==========================================

@app.get("/api/telemetry")
def get_telemetry():

    try:

        # ==================================
        # GET LATEST DATA FROM SUPABASE
        # ==================================

        response = (
            supabase
            .table("telemetry")
            .select("*")
            .order(
                "timestamp",
                desc=True
            )
            .limit(1)
            .execute()
        )


        # ==================================
        # NO DATA
        # ==================================

        if not response.data:

            return {
                "message":
                    "No telemetry data available"
            }


        # ==================================
        # LATEST DATABASE RECORD
        # ==================================

        data = response.data[0]


        # ==================================
        # CALCULATE RELIABILITY
        # ==================================

        reliability = calculate_reliability(
            data
        )


        # ==================================
        # RETURN COMPLETE TELEMETRY
        # ==================================

        return {

            # ------------------------------
            # TIMESTAMP
            # ------------------------------

            "timestamp":
                data.get("timestamp"),


            # ------------------------------
            # ENVIRONMENT
            # ------------------------------

            "temperature":
                data.get("temperature"),

            "pressure":
                data.get("pressure"),

            "altitude":
                data.get("altitude"),


            # ------------------------------
            # INTERNAL TEMPERATURES
            # ------------------------------

            "battery_temperature":
                data.get(
                    "battery_temperature"
                ),

            "electronics_temperature":
                data.get(
                    "electronics_temperature"
                ),


            # ------------------------------
            # BATTERY
            # ------------------------------

            "battery_voltage":
                data.get(
                    "battery_voltage"
                ),

            "battery_current":
                data.get(
                    "battery_current"
                ),


            # ------------------------------
            # LOAD
            # ------------------------------

            "load_voltage":
                data.get(
                    "load_voltage"
                ),

            "load_current":
                data.get(
                    "load_current"
                ),


            # ------------------------------
            # FRONTEND COMPATIBILITY
            # ------------------------------

            "voltage":
                data.get(
                    "load_voltage"
                ),

            "current":
                data.get(
                    "load_current"
                ),


            # ------------------------------
            # DERIVED RELIABILITY DATA
            # ------------------------------

            "rpm":
                reliability["rpm"],

            "rpm_stability":
                reliability["rpm_stability"],

            "temperature_stress":
                reliability["temperature_stress"],

            "pressure_stress":
                reliability["pressure_stress"],

            "current_stress":
                reliability["current_stress"],

            "electronics_stress":
                reliability["electronics_stress"],

            "health":
                reliability["health"],

            "alert_level":
                reliability["alert_level"],

            "alert_message":
                reliability["alert_message"]
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ==========================================
# POST TELEMETRY
# ESP32 / SIMULATOR USES THIS
# ==========================================

@app.post("/api/telemetry")
def receive_telemetry(
    data: Telemetry
):

    try:

        # ==================================
        # CONVERT TO DICTIONARY
        # ==================================

        telemetry_data = {

            "temperature":
                data.temperature,

            "pressure":
                data.pressure,

            "altitude":
                data.altitude,

            "battery_temperature":
                data.battery_temperature,

            "electronics_temperature":
                data.electronics_temperature,

            "battery_voltage":
                data.battery_voltage,

            "battery_current":
                data.battery_current,

            "load_voltage":
                data.load_voltage,

            "load_current":
                data.load_current
        }


        # ==================================
        # STORE IN SUPABASE
        # ==================================

        response = (
            supabase
            .table("telemetry")
            .insert(
                telemetry_data
            )
            .execute()
        )


        # ==================================
        # RESPONSE
        # ==================================

        return {

            "status":
                "success",

            "message":
                "Telemetry stored in Supabase",

            "data":
                response.data
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to store telemetry: "
                f"{str(e)}"
            )
        )