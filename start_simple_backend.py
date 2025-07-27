#!/usr/bin/env python3

"""
Startup script for Horus AI-BI Simple Backend
Handles port conflicts and provides status checking
"""

import socket
import subprocess
import sys
import time
import os

def check_port(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_free_port(start_port=8000, max_attempts=10):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if check_port(port):
            return port
    return None

def test_backend(port):
    """Test if backend is responding"""
    try:
        import urllib.request
        import json
        
        response = urllib.request.urlopen(f'http://localhost:{port}/health', timeout=2)
        data = json.loads(response.read().decode())
        return data.get('status') == 'healthy'
    except:
        return False

def main():
    """Start the backend with proper error handling"""
    
    print("🚀 HORUS AI-BI BACKEND STARTUP")
    print("=" * 40)
    
    # Check if backend is already running
    if test_backend(8000):
        print("✅ Backend already running on port 8000!")
        print("🌐 http://localhost:8000/health")
        print("💬 http://localhost:8000/api/v1/conversational/analyze")
        print("\n🎯 Your frontend should be able to connect now!")
        return
    
    # Find available port
    port = find_free_port(8000, 5)
    if not port:
        print("❌ No free ports found (8000-8004)")
        print("💡 Try killing any existing processes on these ports")
        return
    
    if port != 8000:
        print(f"⚠️  Port 8000 busy, using port {port}")
        print(f"⚠️  Update frontend to use http://localhost:{port}")
    
    # Update the simple_backend.py with the correct port
    backend_script = '/home/maf/maf/Dask/AIBI/simple_backend.py'
    
    with open(backend_script, 'r') as f:
        content = f.read()
    
    # Replace PORT = 8000 with the available port
    content = content.replace('PORT = 8000', f'PORT = {port}')
    
    with open(backend_script, 'w') as f:
        f.write(content)
    
    print(f"🔧 Starting backend on port {port}...")
    print("📋 Server URLs:")
    print(f"   🌐 Main: http://localhost:{port}")
    print(f"   🩺 Health: http://localhost:{port}/health")
    print(f"   💬 Chat: http://localhost:{port}/api/v1/conversational/analyze")
    print("")
    
    if port != 8000:
        print("⚠️  IMPORTANT: Update your frontend MinimalChat.tsx:")
        print(f"   Change: http://localhost:8000")
        print(f"   To:     http://localhost:{port}")
        print("")
    
    print("🎯 Starting server... (Press Ctrl+C to stop)")
    print("=" * 40)
    
    try:
        # Start the backend
        os.system(f'python3 {backend_script}')
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()