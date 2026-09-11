from fastapi import FastAPI
from datetime import datetime
import random

app = FastAPI(title="SIH #49 High Altitude Monitoring")


@app.get("/")
def home():
    return {
        "message": "SIH #49 Backend is running"
    }


@app.get("/api/telemetry")
def telemetry():

    temperature = round(random.uniform(-35, -15), 2)
    pressure = round(random.uniform(50, 65), 2)
    battery = round(random.uniform(10.5, 12.6), 2)
    altitude = round(random.uniform(4000, 5500), 2)
    vibration = round(random.uniform(0.1, 1.0), 2)

    return {
        "timestamp": datetime.now().isoformat(),
        "temperature": temperature,
        "pressure": pressure,
        "battery_voltage": battery,
        "altitude": altitude,
        "vibration": vibration
    }