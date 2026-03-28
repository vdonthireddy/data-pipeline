import json
import os
import time
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
import mysql.connector

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootpassword")
MYSQL_DB = os.getenv("MYSQL_DB", "sensor_db")
TOPIC = "sensor_data"

def get_mysql_connection():
    while True:
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}. Retrying in 5s...")
            time.sleep(5)

def main():
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'mysql-writer-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(**conf)
    consumer.subscribe([TOPIC])

    conn = get_mysql_connection()
    cursor = conn.cursor()

    print(f"Starting mysql-writer, consuming from {TOPIC}...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            # Process message
            data = json.loads(msg.value().decode('utf-8'))
            sensor_type = data['sensor_type']
            value = data['value']
            # handle Z suffix for python < 3.11
            ts_str = data['timestamp'].replace('Z', '+00:00')
            timestamp = datetime.fromisoformat(ts_str)

            # Store in MySQL
            query = "INSERT INTO raw_sensor_data (sensor_type, value, timestamp) VALUES (%s, %s, %s)"
            cursor.execute(query, (sensor_type, value, timestamp))
            conn.commit()
            
            print(f"Stored: {sensor_type} = {value}")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
