import time
import json
import random
import os
import requests
from datetime import datetime
from confluent_kafka import Producer

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
TOPIC = "sensor_data"
SENSOR_TYPES = ["temperature", "pressure", "vibration", "acoustic"]

def get_sensor_value(sensor_type):
    if sensor_type == "temperature":
        return random.uniform(20.0, 110.0)
    elif sensor_type == "pressure":
        return random.uniform(90.0, 160.0)
    elif sensor_type == "vibration":
        return random.uniform(0.1, 15.0)
    elif sensor_type == "acoustic":
        return random.uniform(40.0, 100.0)
    return 0.0

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def get_status():
    try:
        response = requests.get(f"{BACKEND_URL}/simulator/status", timeout=5)
        data = response.json()
        return data.get("active", True), data.get("interval", 30)
    except Exception as e:
        print(f"Error checking status: {e}")
        return True, 30 # Default

def main():
    conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
    producer = Producer(**conf)

    print(f"Starting simulator sending to {KAFKA_BOOTSTRAP_SERVERS}...")

    while True:
        active, interval = get_status()
        
        if not active:
            print("Simulator is paused...")
            time.sleep(5)
            continue

        print(f"Generating data (interval: {interval}s)...")
        for sensor in SENSOR_TYPES:
            data = {
                "sensor_type": sensor,
                "value": get_sensor_value(sensor),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Using sensor as key to ensure sequential order in the same partition
            producer.produce(
                TOPIC, 
                key=sensor, 
                value=json.dumps(data).encode('utf-8'),
                callback=delivery_report
            )
            producer.poll(0)
            
        producer.flush()
        time.sleep(interval)

if __name__ == "__main__":
    main()
