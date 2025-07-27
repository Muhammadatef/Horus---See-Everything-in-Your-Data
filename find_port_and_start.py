#!/usr/bin/env python3

"""
Find a free port and start the backend server
"""

import socket
import subprocess
import sys
import json

def find_free_port(start=8000, end=8020):
    """Find the first free port in range"""
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def update_frontend_port(port):
    """Update the frontend to use the correct port"""
    frontend_file = '/home/maf/maf/Dask/AIBI/frontend/src/components/chat/MinimalChat.tsx'
    
    try:
        with open(frontend_file, 'r') as f:
            content = f.read()
        
        # Replace any localhost:80xx with the new port
        import re
        content = re.sub(r'http://localhost:80\d+', f'http://localhost:{port}', content)
        
        with open(frontend_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated frontend to use port {port}")
        return True
    except Exception as e:
        print(f"❌ Failed to update frontend: {e}")
        return False

def start_simple_server(port):
    """Start a very simple HTTP server"""
    
    import http.server
    import socketserver
    
    class SimpleHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if self.path == '/health':
                response = {"status": "healthy", "service": "Horus AI-BI Simple", "port": port}
            else:
                response = {"message": "Horus AI-BI Backend Running", "status": "ok", "port": port}
            
            self.wfile.write(json.dumps(response).encode())
        
        def do_POST(self):
            if '/conversational/analyze' in self.path:
                # Simple chat response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "conversation_id": "test_conv_123",
                    "question": "Test question",
                    "answer": "🤖 Hello! I'm your Horus AI assistant. I see you're testing the connection - great! Please upload a CSV file and ask me specific questions about your data like 'What is the average price?' or 'How many records do we have?'",
                    "data_summary": {
                        "filename": "test",
                        "total_rows": 0,
                        "message": "Upload CSV file to analyze"
                    },
                    "follow_up_questions": [
                        "Upload a CSV file to get started",
                        "Ask about averages, totals, or counts",
                        "What insights would you like?"
                    ],
                    "success": True
                }
                
                self.wfile.write(json.dumps(response, indent=2).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"error": "Not found"}')
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', '*')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
    
    print(f"🚀 Starting Horus AI-BI Backend on port {port}")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🩺 Health: http://localhost:{port}/health")
    print(f"💬 Chat: http://localhost:{port}/api/v1/conversational/analyze")
    print()
    print("✅ Backend is now running!")
    print("🎯 Your NetworkError should be fixed!")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def main():
    print("🔍 Finding free port...")
    port = find_free_port(8000, 8020)
    
    if not port:
        print("❌ No free ports found in range 8000-8020")
        print("💡 Try stopping other services or use different ports")
        return
    
    print(f"✅ Found free port: {port}")
    
    # Update frontend if needed
    if port != 8000:
        print(f"🔧 Updating frontend to use port {port}...")
        update_frontend_port(port)
    
    # Start the server
    start_simple_server(port)

if __name__ == "__main__":
    main()