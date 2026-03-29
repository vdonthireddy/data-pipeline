#!/bin/bash

echo "Waiting for Kafka brokers to be ready..."

# Wait for all three brokers to be reachable on their internal ports
until nc -z kafka-1 29092 && nc -z kafka-2 29092 && nc -z kafka-3 29092; do
  echo "Kafka brokers are not ready yet... sleeping 2s"
  sleep 2
done

echo "Kafka brokers are up! Creating topic 'sensor_data' with 4 partitions and replication factor 3..."

# Create the sensor_data topic
/opt/kafka/bin/kafka-topics.sh --create --if-not-exists --bootstrap-server kafka-1:29092 --partitions 4 --replication-factor 3 --topic sensor_data

echo "Topic creation command sent."
