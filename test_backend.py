#!/usr/bin/env python3

"""
Quick test of the backend chat endpoint
"""

import urllib.request
import urllib.parse
import json

def test_chat():
    """Test the chat endpoint with sample CSV data"""
    
    # Sample CSV data
    csv_data = """product_name,price,category,rating
iPhone 14,999.99,Electronics,4.8
Samsung TV,799.99,Electronics,4.5
Nike Shoes,129.99,Fashion,4.3"""
    
    # Create multipart form data
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
    
    try:
        req = urllib.request.Request(
            'http://localhost:8003/api/v1/conversational/analyze',
            data=form_data.encode(),
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
            }
        )
        
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode())
        
        print("✅ Backend chat test successful!")
        print(f"Question: {data.get('question')}")
        print(f"Answer: {data.get('answer')}")
        print(f"Success: {data.get('success')}")
        print(f"Conversation ID: {data.get('conversation_id')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend chat test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Backend Chat Endpoint on Port 8003")
    print("=" * 50)
    test_chat()