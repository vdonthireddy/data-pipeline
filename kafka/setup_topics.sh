#!/bin/bash

echo "Waiting for Kafka (KRaft) to be ready..."
# Simple wait loop for Kafka port
while ! nc -z kafka 29092; do
  sleep 1
done

echo "Kafka is up! Creating topic..."

# Create the sensor_data topic with 4 partitions
/opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server kafka:29092 --partitions 4 --replication-factor 1 --topic sensor_data
