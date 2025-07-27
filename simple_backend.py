#!/usr/bin/env python3

"""
Ultra-Simple Backend Server for Horus AI-BI Platform
Works with Python 3.13+ without any external dependencies
"""

import http.server
import socketserver
import json
import re

class SimpleHorusHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if self.path == '/health':
                response = {
                    "status": "healthy",
                    "service": "Horus AI-BI Platform (Simple)",
                    "version": "1.0.0-simple"
                }
            else:
                response = {
                    "message": "🤖 Horus AI-BI Platform Backend is Running!",
                    "status": "operational",
                    "endpoints": {
                        "health": "/health", 
                        "chat": "/api/v1/conversational/analyze"
                    },
                    "note": "Simple backend for testing - upload CSV and ask questions!"
                }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self.send_404()
    
    def do_POST(self):
        """Handle POST requests"""
        
        if self.path == '/api/v1/conversational/analyze':
            self.handle_chat()
        elif self.path == '/api/v1/conversational/continue':
            self.handle_continue_chat()
        else:
            self.send_404()
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def handle_chat(self):
        """Handle chat requests with file upload"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise Exception("No data received")
            
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            # Simple parsing of multipart form data
            question = self.extract_field(post_data, 'question', 'What can you tell me about this data?')
            user_id = self.extract_field(post_data, 'user_id', 'anonymous')
            
            # Look for CSV data in the file field
            csv_data = self.extract_csv_data(post_data)
            
            # Generate conversation ID
            conv_id = f"conv_{hash(user_id + question) % 100000}"
            
            # Analyze the data and generate response
            if csv_data and len(csv_data.strip()) > 20:
                analysis = self.analyze_simple_csv(csv_data, question)
                answer = analysis['answer']
                data_summary = analysis['summary']
            else:
                answer = "I don't see any CSV data in your upload. Please upload a CSV file with your question. I can analyze data and answer questions like 'What is the average price?' or 'How many rows are there?'"
                data_summary = {
                    "filename": "no_file_uploaded",
                    "total_rows": 0,
                    "total_columns": 0,
                    "message": "Please upload a CSV file"
                }
            
            response = {
                "conversation_id": conv_id,
                "question": question,
                "answer": answer,
                "data_summary": data_summary,
                "visualization": {"type": "none", "message": "Upload CSV data for visualizations"},
                "follow_up_questions": [
                    "What is the average value?",
                    "How many records do we have?",
                    "What's the highest value?",
                    "Can you summarize the data?"
                ],
                "conversation_context": {
                    "file_analyzed": csv_data is not None,
                    "data_schema": {}
                },
                "success": True
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(f"Chat error: {str(e)}")
    
    def handle_continue_chat(self):
        """Handle follow-up chat requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            question = self.extract_field(post_data, 'question', 'Follow-up question')
            conv_id = self.extract_field(post_data, 'conversation_id', 'unknown')
            
            # For follow-up questions, provide contextual responses
            answer = f"This is a follow-up question in conversation {conv_id}: '{question}'. In a full implementation, I would reference our previous conversation and provide contextual analysis. For now, please ask specific questions about your data!"
            
            response = {
                "conversation_id": conv_id,
                "question": question,
                "answer": answer,
                "follow_up_questions": [
                    "What other insights can you find?",
                    "How does this compare to previous results?",
                    "Can you dig deeper into this data?",
                    "What should I focus on next?"
                ],
                "success": True
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(f"Continue chat error: {str(e)}")
    
    def extract_field(self, data, field_name, default=''):
        """Extract a form field from multipart data"""
        pattern = f'name="{field_name}".*?\r?\n\r?\n(.*?)(?=\r?\n--|\r?\n$|$)'
        match = re.search(pattern, data, re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
    
    def extract_csv_data(self, data):
        """Extract CSV data from file upload"""
        # Look for file content after filename
        if 'filename=' in data and '.csv' in data:
            # Find the start of CSV data (after double newline)
            parts = data.split('\r\n\r\n')
            for part in parts:
                # Look for parts that look like CSV (comma-separated, multiple lines)
                if ',' in part and '\n' in part and len(part.strip()) > 20:
                    lines = part.strip().split('\n')
                    if len(lines) >= 2:  # At least header + one data row
                        return part.strip()
        return None
    
    def analyze_simple_csv(self, csv_data, question):
        """Simple CSV analysis"""
        try:
            lines = [line.strip() for line in csv_data.split('\n') if line.strip()]
            if len(lines) < 2:
                raise Exception("Need at least header and data rows")
            
            # Parse headers and data
            headers = [h.strip().strip('"') for h in lines[0].split(',')]
            data_rows = []
            
            for line in lines[1:]:
                row = [cell.strip().strip('"') for cell in line.split(',')]
                if len(row) == len(headers):
                    data_rows.append(dict(zip(headers, row)))
            
            # Simple numeric analysis
            numeric_stats = {}
            for header in headers:
                values = []
                for row in data_rows:
                    try:
                        val = float(row[header])
                        values.append(val)
                    except (ValueError, TypeError):
                        pass
                
                if values:
                    numeric_stats[header] = {
                        'count': len(values),
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
            
            # Generate specific answer
            answer = self.generate_specific_answer(question, numeric_stats, data_rows, headers)
            
            return {
                'answer': answer,
                'summary': {
                    'filename': 'uploaded_data.csv',
                    'total_rows': len(data_rows),
                    'total_columns': len(headers),
                    'columns': headers,
                    'sample_data': data_rows[:3]
                }
            }
            
        except Exception as e:
            return {
                'answer': f"I had trouble analyzing your CSV: {str(e)}. Please ensure it's properly formatted.",
                'summary': {'error': str(e)}
            }
    
    def generate_specific_answer(self, question, numeric_stats, data_rows, headers):
        """Generate specific answers based on question"""
        q = question.lower()
        
        # Handle average price questions
        if 'average' in q and 'price' in q:
            if 'price' in numeric_stats:
                avg = numeric_stats['price']['average']
                min_val = numeric_stats['price']['min']
                max_val = numeric_stats['price']['max']
                return f"The **average price** in your dataset is **${avg:.2f}**. The price range is ${min_val:.2f} to ${max_val:.2f}."
            else:
                return f"I don't see a 'price' column. Available columns: {', '.join(headers)}"
        
        # Handle highest/maximum questions
        elif any(word in q for word in ['highest', 'maximum', 'max']):
            if 'price' in q and 'price' in numeric_stats:
                return f"The **highest price** is **${numeric_stats['price']['max']:.2f}**."
            elif 'rating' in q and 'rating' in numeric_stats:
                return f"The **highest rating** is **{numeric_stats['rating']['max']:.1f}**."
            else:
                return "Please specify which column you want the maximum for: " + ", ".join(headers)
        
        # Handle count questions
        elif any(word in q for word in ['how many', 'count', 'total']):
            return f"Your dataset has **{len(data_rows)} rows** and **{len(headers)} columns**. Columns: {', '.join(headers)}"
        
        # General analysis
        else:
            parts = [f"I analyzed your CSV with **{len(data_rows)} rows** and **{len(headers)} columns**."]
            
            if numeric_stats:
                parts.append("\n**Numeric Analysis:**")
                for col, stats in numeric_stats.items():
                    parts.append(f"• {col}: avg={stats['average']:.2f}, range={stats['min']:.2f}-{stats['max']:.2f}")
            
            parts.append(f"\n**Available columns:** {', '.join(headers)}")
            parts.append("\nAsk me specific questions like 'What is the average price?' or 'How many rows?'")
            
            return "".join(parts)
    
    def send_json_response(self, data):
        """Send JSON response with CORS headers"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_error_response(self, message):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"error": message, "success": False}
        self.wfile.write(json.dumps(response).encode())
    
    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"error": "Endpoint not found"}
        self.wfile.write(json.dumps(response).encode())

def main():
    """Start the simple backend server"""
    PORT = 8001  # Use different port since 8000 is occupied
    
    print("🚀 HORUS AI-BI SIMPLE BACKEND SERVER")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:{PORT}")
    print(f"🩺 Health: http://localhost:{PORT}/health")
    print(f"💬 Chat API: http://localhost:{PORT}/api/v1/conversational/analyze")
    print("")
    print("✅ No external dependencies required!")
    print("✅ Works with Python 3.13+")
    print("✅ Supports CSV file upload and analysis")
    print("✅ Answers specific questions about your data")
    print("")
    print("📝 Ready for your frontend to connect!")
    print("🎯 Your NetworkError should be fixed now!")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleHorusHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == "__main__":
    main()