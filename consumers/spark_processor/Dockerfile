FROM bitnamilegacy/spark:3.4

USER root
RUN pip install --no-cache-dir pyspark mysql-connector-python

WORKDIR /app
COPY . .

# Set spark submit command
# Needs spark-sql-kafka-0-10_2.12 and kafka-clients
CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", "spark_job.py"]
