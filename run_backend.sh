#!/bin/bash

echo "🚀 Starting Horus AI-BI Backend Server"
echo "====================================="

cd /home/maf/maf/Dask/AIBI

# Kill any existing processes on port 8000
echo "🔧 Checking for existing processes on port 8000..."
pkill -f "simple_backend.py" 2>/dev/null || true
sleep 1

# Start the backend
echo "🔥 Starting backend server..."
echo "📡 Server will be available at: http://localhost:8000"
echo "🩺 Health check: http://localhost:8000/health"
echo "💬 Chat API: http://localhost:8000/api/v1/conversational/analyze"
echo ""
echo "📝 Your frontend NetworkError should be fixed!"
echo "🎯 Test with: curl http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "====================================="

python3 simple_backend.py