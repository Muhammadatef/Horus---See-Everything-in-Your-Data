#!/usr/bin/env python3

"""
Test the simple backend server
"""

import urllib.request
import urllib.parse
import json
import time

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
        data = json.loads(response.read().decode())
        print("✅ Health endpoint working:")
        print(f"   Status: {data.get('status')}")
        print(f"   Service: {data.get('service')}")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint with sample data"""
    try:
        # Create sample CSV data
        csv_data = """product_name,price,category,rating
iPhone 14,999.99,Electronics,4.8
Samsung TV,799.99,Electronics,4.5
Nike Shoes,129.99,Fashion,4.3"""
        
        # Create multipart form data manually
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        
        form_data = f'''------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="question"\r
\r
What is the average price?\r
------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="user_id"\r
\r
test_user\r
------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="file"; filename="test.csv"\r
Content-Type: text/csv\r
\r
{csv_data}\r
------WebKitFormBoundary7MA4YWxkTrZu0gW--\r
'''
        
        # Create request
        req = urllib.request.Request(
            'http://localhost:8000/api/v1/conversational/analyze',
            data=form_data.encode(),
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
            }
        )
        
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode())
        
        print("✅ Chat endpoint working:")
        print(f"   Question: {data.get('question')}")
        print(f"   Answer: {data.get('answer', 'No answer')[:100]}...")
        print(f"   Success: {data.get('success')}")
        return True
        
    except Exception as e:
        print(f"❌ Chat endpoint failed: {e}")
        return False

def main():
    print("🧪 TESTING SIMPLE BACKEND")
    print("=" * 40)
    print("Make sure the backend is running first!")
    print("Run: ./run_backend.sh")
    print()
    
    # Test health
    print("1. Testing health endpoint...")
    health_ok = test_health_endpoint()
    
    if health_ok:
        print("\n2. Testing chat endpoint...")
        chat_ok = test_chat_endpoint()
        
        if chat_ok:
            print("\n🎉 BACKEND IS WORKING!")
            print("✅ Your frontend NetworkError should be fixed")
            print("✅ You can now upload CSV and ask questions")
        else:
            print("\n⚠️  Health OK but chat endpoint has issues")
    else:
        print("\n❌ Backend not responding")
        print("💡 Make sure to run: ./run_backend.sh first")

if __name__ == "__main__":
    main()