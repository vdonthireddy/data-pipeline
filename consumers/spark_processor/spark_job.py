import os
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import mysql.connector

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootpassword")
MYSQL_DB = os.getenv("MYSQL_DB", "sensor_db")
TOPIC = "sensor_data"

def write_to_mysql(batch_df, batch_id):
    # Rule logic
    # temperature > 80: High Temperature Warning.
    # pressure > 150: High Pressure Warning.
    # vibration > 10: Unusual Vibration Alert.
    # acoustic > 90: High Noise Level.
    
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()
    
    rows = batch_df.collect()
    for row in rows:
        sensor_type = row.sensor_type
        value = row.value
        timestamp = row.timestamp
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
            query = "INSERT INTO notifications (sensor_type, value, message, timestamp) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (sensor_type, value, message, timestamp))
            print(f"Notification: {sensor_type} = {value} - {message}")
            
    conn.commit()
    cursor.close()
    conn.close()

def main():
    spark = SparkSession.builder \
        .appName("SensorProcessor") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    # Define schema
    schema = StructType([
        StructField("sensor_type", StringType(), True),
        StructField("value", DoubleType(), True),
        StructField("timestamp", StringType(), True)
    ])

    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", TOPIC) \
        .load()

    # Parse JSON
    sensor_df = df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*")
    
    # Cast timestamp (Spark should handle 'Z' suffix correctly with to_timestamp)
    from pyspark.sql.functions import to_timestamp
    sensor_df = sensor_df.withColumn("timestamp", to_timestamp(col("timestamp")))

    # Process and write to MySQL
    query = sensor_df.writeStream \
        .foreachBatch(write_to_mysql) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
