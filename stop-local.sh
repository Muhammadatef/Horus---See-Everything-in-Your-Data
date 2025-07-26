#!/bin/bash

echo "🛑 Stopping Local AI-BI Platform..."

# Stop all services
docker-compose down

echo "🧹 Cleaning up..."

# Optional: Remove unused images and containers
read -p "Remove unused Docker images and containers? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker system prune -f
    echo "✅ Cleanup completed"
fi

echo "✅ Platform stopped successfully"