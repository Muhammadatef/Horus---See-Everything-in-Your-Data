#!/bin/bash

# Backend startup script for Horus AI-BI Platform

echo "🚀 Starting Horus AI-BI Backend..."
echo "=================================="

# Navigate to backend directory
cd /home/maf/maf/Dask/AIBI/backend

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not found. Installing dependencies..."
    echo "📥 Installing Python packages..."
    
    # Try different installation methods
    if pip3 install --user -r requirements.txt; then
        echo "✅ Dependencies installed successfully"
    elif python3 -m pip install --user -r requirements.txt; then
        echo "✅ Dependencies installed successfully (method 2)"
    elif pip3 install --user --break-system-packages -r requirements.txt; then
        echo "✅ Dependencies installed successfully (method 3)"
    else
        echo "❌ Failed to install dependencies"
        echo "💡 Try manually: pip3 install --user fastapi uvicorn pandas"
        exit 1
    fi
else
    echo "✅ Dependencies already installed"
fi

# Create marker file
touch .deps_installed

echo ""
echo "🔥 Starting FastAPI server..."
echo "📡 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🗣️  Chat API: http://localhost:8000/api/v1/conversational/analyze"
echo ""
echo "💡 In another terminal, start frontend with:"
echo "   cd /home/maf/maf/Dask/AIBI/frontend && npm start"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

# Start the FastAPI server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload