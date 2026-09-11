from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import random

app = FastAPI()


# -----------------------------
# Telemetry data structure
# -----------------------------
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


# -----------------------------
# Home endpoint
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "SIH #49 Backend is running"
    }


# -----------------------------
# GET telemetry
# Temporary simulator
# -----------------------------
@app.get("/api/telemetry")
def get_telemetry():

    return {
        "timestamp": datetime.now().isoformat(),

        "temperature": round(random.uniform(-35, -10), 2),
        "pressure": round(random.uniform(45, 65), 2),
        "altitude": round(random.uniform(4000, 6000), 2),

        "battery_temperature": round(random.uniform(-20, 0), 2),
        "electronics_temperature": round(random.uniform(-15, 5), 2),

        "battery_voltage": round(random.uniform(11.5, 12.6), 2),
        "battery_current": round(random.uniform(0.3, 1.5), 2),

        "load_voltage": round(random.uniform(11.0, 12.2), 2),
        "load_current": round(random.uniform(0.2, 1.2), 2)
    }


# -----------------------------
# POST telemetry
# ESP32 will use this later
# -----------------------------
@app.post("/api/telemetry")
def receive_telemetry(data: Telemetry):

    return {
        "status": "success",
        "message": "Telemetry received",
        "timestamp": datetime.now().isoformat(),
        "data": data
    }