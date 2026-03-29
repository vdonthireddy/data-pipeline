#!/bin/bash

echo "🧹 Cleaning up Sensor Data Pipeline..."

# Stop and remove containers, networks, and volumes
docker compose down --remove-orphans -v

# Optional: clean up unused images to free space
echo "Reclaiming disk space..."
docker system prune -f

echo "----------------------------------------"
echo "✅ Cleanup complete! All services stopped and removed."
echo "----------------------------------------"
