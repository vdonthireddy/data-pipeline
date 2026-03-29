import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from aiokafka import AIOKafkaConsumer

# Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootpassword")
MYSQL_DB = os.getenv("MYSQL_DB", "sensor_db")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:29092,kafka-2:29092,kafka-3:29092")

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
    id: Optional[int] = None
    sensor_type: str
    value: float
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        }

class Notification(BaseModel):
    id: Optional[int] = None
    sensor_type: str
    value: float
    message: str
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        }

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed
                pass

manager = ConnectionManager()

async def kafka_consumer_task():
    topic = "sensor_data"
    print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
    
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="backend-ws-group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    connected = False
    while not connected:
        try:
            await consumer.start()
            connected = True
            print("Kafka consumer started successfully!")
        except Exception as e:
            print(f"Failed to start Kafka consumer: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

    try:
        async for msg in consumer:
            data = msg.value
            
            # Broadcast raw sensor data
            await manager.broadcast({
                "type": "sensor_data",
                "data": data
            })
            
            # Derived notification logic (same as Spark job)
            sensor_type = data.get("sensor_type")
            value = data.get("value", 0)
            timestamp = data.get("timestamp")
            message = ""
            
            if sensor_type == "temperature" and value > 80:
                message = "High Temperature Warning"
            elif sensor_type == "pressure" and value > 150:
                message = "High Pressure Warning"
            elif sensor_type == "vibration" and value > 10:
                message = "Unusual Vibration Alert"
            elif sensor_type == "acoustic" and value > 90:
                message = "High Noise Level"
            
            if message:
                notification = {
                    "sensor_type": sensor_type,
                    "value": value,
                    "message": message,
                    "timestamp": timestamp
                }
                await manager.broadcast({
                    "type": "notification",
                    "data": notification
                })
    except Exception as e:
        print(f"Kafka consumer error: {e}")
    finally:
        await consumer.stop()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_consumer_task())

@app.get("/")
def read_root():
    return {"message": "Sensor API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
