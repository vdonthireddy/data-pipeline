#!/bin/bash

echo "🚀 Starting Sensor Data Pipeline..."

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start services
docker compose up -d --build

echo "----------------------------------------"
echo "✅ Services are starting up!"
echo ""
echo "📊 React UI:     http://localhost:3000"
echo "🔌 Backend API:  http://localhost:8000"
echo "📜 API Docs:     http://localhost:8000/docs"
echo "----------------------------------------"
echo "Wait a few seconds for Kafka and MySQL to initialize..."
echo "Check logs with: docker compose logs -f"
