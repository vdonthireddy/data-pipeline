# Real-time Sensor Data Pipeline (Enterprise Edition)

A highly available end-to-end data pipeline with multi-node Kafka, real-time WebSockets, and full monitoring.

## 🚀 New Features

- **High Availability (HA):** 3-node Kafka cluster in KRaft mode with replication factor 3. The pipeline stays alive even if a broker fails.
- **Real-time WebSockets:** Low-latency live data streaming directly from Kafka to the UI via FastAPI WebSockets.
- **Observability Stack:** Integrated **Prometheus** and **Grafana** for monitoring Kafka throughput, consumer lag, and Spark performance.
- **Improved UI:** Polling has been replaced with persistent WebSockets for instantaneous updates.

## 🏗 Architecture & Data Flow

```mermaid
flowchart TD
    User --> UI[Frontend - React/Nginx]
    UI <--> |WebSocket| API[Backend - FastAPI]
    API --> DB[(MySQL Database)]
    API -- Control --> Sim[Simulator - Python]
    
    subgraph KafkaCluster [Kafka Cluster: 3 Brokers | Replication: 3]
        direction LR
        K1[Broker 1]
        K2[Broker 2]
        K3[Broker 3]
    end

    Sim -- "Keyed" --> KafkaCluster
    
    KafkaCluster --> Writer[MySQL Writer]
    KafkaCluster --> Spark[Spark Processor]
    KafkaCluster --> API
    
    subgraph Monitoring
        Prom[Prometheus] --> KExp[Kafka Exporter]
        KExp --> KafkaCluster
        Prom --> Spark
        Graf[Grafana] --> Prom
    end
    
    Writer --> DB
    Spark --> DB
```

## 🛠 Monitoring Endpoints

- **Grafana Dashboard:** [http://localhost:3001](http://localhost:3001) (Default user/pass: `admin/admin`)
- **Prometheus UI:** [http://localhost:9090](http://localhost:9090)
- **Kafka Exporter:** [http://localhost:9308/metrics](http://localhost:9308/metrics)

## 🏁 Quick Start

1.  Ensure **Docker** is running and you have enough memory (at least 4GB recommended for the full cluster).
2.  Launch the pipeline:
    ```bash
    chmod +x quickstart.sh
    ./quickstart.sh
    ```
3.  **Dashboard:** [http://localhost:3000](http://localhost:3000)
4.  **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## 📁 Project Structure

- `/simulator`: Kafka Producer with control logic.
- `/consumers/mysql_writer`: Python consumer for persistence.
- `/consumers/spark_processor`: PySpark streaming rules engine.
- `/backend`: FastAPI service with **WebSocket Manager**.
- `/frontend`: React dashboard with **WebSocket Client**.
- `/monitoring`: Prometheus configuration.
- `docker-compose.yml`: Orchestration for 12+ containers.
