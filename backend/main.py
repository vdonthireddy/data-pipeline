import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootpassword")
MYSQL_DB = os.getenv("MYSQL_DB", "sensor_db")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

class SensorData(BaseModel):
    id: int
    sensor_type: str
    value: float
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        }

class Notification(BaseModel):
    id: int
    sensor_type: str
    value: float
    message: str
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        }

@app.get("/")
def read_root():
    return {"message": "Sensor API is running"}

# Global state for simulator
simulator_active = True
simulator_interval = 5

@app.get("/simulator/status")
def get_simulator_status():
    return {"active": simulator_active, "interval": simulator_interval}

@app.post("/simulator/pause")
def pause_simulator():
    global simulator_active
    simulator_active = False
    return {"message": "Simulator paused", "active": False}

@app.post("/simulator/resume")
def resume_simulator():
    global simulator_active
    simulator_active = True
    return {"message": "Simulator resumed", "active": True}

@app.post("/simulator/interval")
def set_simulator_interval(seconds: int):
    global simulator_interval
    if seconds < 5:
        seconds = 5
    elif seconds > 30:
        seconds = 30
    simulator_interval = seconds
    return {"message": f"Interval set to {seconds}s", "interval": simulator_interval}

@app.get("/data", response_model=List[SensorData])
def get_sensor_data(limit: int = 50, sensor_type: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM raw_sensor_data"
    params = []
    if sensor_type:
        query += " WHERE sensor_type = %s"
        params.append(sensor_type)
    
    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results

@app.get("/notifications", response_model=List[Notification])
def get_notifications(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM notifications ORDER BY timestamp DESC LIMIT %s"
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results
