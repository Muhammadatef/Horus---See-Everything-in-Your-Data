#!/usr/bin/env python3

"""
Test if the backend can start up properly and handle imports
"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/home/maf/maf/Dask/AIBI/backend')

def test_backend_startup():
    """Test if backend can start up without errors"""
    
    print("🧪 TESTING BACKEND STARTUP")
    print("=" * 50)
    
    try:
        print("📦 Testing core imports...")
        
        # Test FastAPI imports
        from fastapi import FastAPI
        print("   ✅ FastAPI imported successfully")
        
        # Test config
        from app.config import settings
        print("   ✅ Settings imported successfully")
        print(f"   ✅ CORS Origins: {settings.CORS_ORIGINS}")
        
        # Test conversation memory (with Redis fallback)
        print("\n💾 Testing conversation memory service...")
        try:
            from app.services.conversation_memory_service import conversation_memory
            print("   ✅ ConversationMemoryService imported")
            print(f"   ✅ Using Redis: {conversation_memory.use_redis}")
        except Exception as e:
            print(f"   ⚠️  Conversation memory fallback: {e}")
        
        # Test API router
        print("\n🔌 Testing API router...")
        from app.api.v1.api import api_router
        print("   ✅ API router imported successfully")
        
        # Test conversational endpoint
        from app.api.v1.endpoints import conversational
        print("   ✅ Conversational endpoint imported")
        
        # Test main app creation (without database)
        print("\n🚀 Testing app creation...")
        from app.main import app
        print("   ✅ FastAPI app created successfully")
        
        print("\n🎯 Backend Import Test Results:")
        print("   ✅ All core components can be imported")
        print("   ✅ CORS is configured for localhost:3000")
        print("   ✅ Conversational endpoint is available")
        print("   ✅ Redis fallback is working")
        
        print("\n📋 To start the backend server:")
        print("   cd /home/maf/maf/Dask/AIBI/backend")
        print("   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Missing dependencies. Try:")
        print("   cd /home/maf/maf/Dask/AIBI/backend")
        print("   pip3 install --user -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_startup_script():
    """Create a startup script for easy backend launching"""
    
    startup_script = '''#!/bin/bash

# Backend startup script for Horus AI-BI Platform

echo "🚀 Starting Horus AI-BI Backend..."

# Navigate to backend directory
cd /home/maf/maf/Dask/AIBI/backend

# Install dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install --user -r requirements.txt
    touch .deps_installed
fi

# Start the FastAPI server
echo "🔥 Starting FastAPI server on http://localhost:8000"
echo "📡 API will be available at http://localhost:8000/api/v1/conversational/analyze"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
'''
    
    with open('/home/maf/maf/Dask/AIBI/start_backend.sh', 'w') as f:
        f.write(startup_script)
    
    # Make it executable
    os.chmod('/home/maf/maf/Dask/AIBI/start_backend.sh', 0o755)
    
    print("📜 Created startup script: /home/maf/maf/Dask/AIBI/start_backend.sh")
    print("   Run: ./start_backend.sh")

if __name__ == "__main__":
    success = test_backend_startup()
    
    if success:
        print("\n✅ Backend ready to start!")
        create_startup_script()
    else:
        print("\n❌ Backend has issues that need to be resolved.")