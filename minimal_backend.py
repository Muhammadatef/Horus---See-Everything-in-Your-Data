#!/usr/bin/env python3

"""
Minimal Backend Server for Horus AI-BI Platform
This is a simple HTTP server that works without FastAPI dependencies
"""

import http.server
import socketserver
import json
import urllib.parse
import cgi
import io
import csv
from urllib.parse import urlparse, parse_qs

class HorusRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "message": "Horus AI-BI Platform Backend",
                "status": "running",
                "endpoints": {
                    "health": "/health",
                    "chat": "/api/v1/conversational/analyze"
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "Horus AI-BI Platform",
                "version": "1.0.0-minimal"
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        
        if self.path == '/api/v1/conversational/analyze':
            self.handle_chat_request()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_chat_request(self):
        """Handle the conversational analyze request"""
        try:
            # Parse form data
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' in content_type:
                # Parse multipart form data
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Simple multipart parsing (basic implementation)
                boundary = content_type.split('boundary=')[1].encode()
                parts = post_data.split(b'--' + boundary)
                
                form_data = {}
                csv_data = None
                
                for part in parts:
                    if b'Content-Disposition' in part:
                        # Extract field name and data
                        lines = part.split(b'\r\n')
                        header_line = None
                        data_start = None
                        
                        for i, line in enumerate(lines):
                            if b'Content-Disposition' in line:
                                header_line = line.decode()
                            elif line == b'' and header_line:
                                data_start = i + 1
                                break
                        
                        if header_line and data_start:
                            # Extract field name
                            if 'name="question"' in header_line:
                                question_data = b'\r\n'.join(lines[data_start:]).strip()
                                form_data['question'] = question_data.decode()
                            elif 'name="user_id"' in header_line:
                                user_data = b'\r\n'.join(lines[data_start:]).strip()
                                form_data['user_id'] = user_data.decode()
                            elif 'name="file"' in header_line:
                                file_data = b'\r\n'.join(lines[data_start:]).strip()
                                csv_data = file_data.decode()
                
                # Process the request
                question = form_data.get('question', 'What can you tell me about this data?')
                user_id = form_data.get('user_id', 'anonymous')
                
                # Analyze CSV data if provided
                analysis_result = self.analyze_csv_data(csv_data, question)
                
                # Generate response
                response = {
                    "conversation_id": f"conv_{hash(user_id + question) % 10000}",
                    "question": question,
                    "answer": analysis_result['answer'],
                    "data_summary": analysis_result['summary'],
                    "visualization": analysis_result.get('visualization'),
                    "follow_up_questions": [
                        "What is the highest value in this dataset?",
                        "Can you show me a breakdown by category?",
                        "What patterns do you see in the data?",
                        "What insights would help with business decisions?"
                    ],
                    "success": True
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, indent=2).encode())
                
            else:
                raise Exception("Invalid content type")
                
        except Exception as e:
            # Error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "error": f"Failed to process request: {str(e)}",
                "success": False
            }
            self.wfile.write(json.dumps(response).encode())
    
    def analyze_csv_data(self, csv_data, question):
        """Simple CSV analysis without external dependencies"""
        
        if not csv_data or len(csv_data.strip()) < 10:
            return {
                "answer": "I don't see any CSV data to analyze. Please upload a CSV file and ask your question again.",
                "summary": {"message": "No data provided"}
            }
        
        try:
            # Parse CSV data
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                raise Exception("CSV needs at least headers and one data row")
            
            # Get headers
            headers = [h.strip() for h in lines[0].split(',')]
            
            # Parse data rows
            data_rows = []
            for line in lines[1:]:
                if line.strip():
                    row = [cell.strip() for cell in line.split(',')]
                    if len(row) == len(headers):
                        data_rows.append(dict(zip(headers, row)))
            
            # Perform simple analysis
            total_rows = len(data_rows)
            
            # Look for numeric columns
            numeric_analysis = {}
            for header in headers:
                numeric_values = []
                for row in data_rows:
                    try:
                        value = float(row[header])
                        numeric_values.append(value)
                    except (ValueError, TypeError):
                        pass
                
                if numeric_values:
                    numeric_analysis[header] = {
                        'count': len(numeric_values),
                        'average': sum(numeric_values) / len(numeric_values),
                        'min': min(numeric_values),
                        'max': max(numeric_values)
                    }
            
            # Generate answer based on question
            answer = self.generate_answer(question, numeric_analysis, data_rows, headers)
            
            return {
                "answer": answer,
                "summary": {
                    "filename": "uploaded_data.csv",
                    "total_rows": total_rows,
                    "total_columns": len(headers),
                    "columns": headers,
                    "numeric_columns": list(numeric_analysis.keys()),
                    "sample_data": data_rows[:3]
                },
                "visualization": {
                    "type": "table",
                    "title": "Data Summary",
                    "data": data_rows[:5]
                }
            }
            
        except Exception as e:
            return {
                "answer": f"I had trouble analyzing your CSV data: {str(e)}. Please make sure it's properly formatted with headers and comma-separated values.",
                "summary": {"error": str(e)}
            }
    
    def generate_answer(self, question, numeric_analysis, data_rows, headers):
        """Generate a specific answer based on the question and data"""
        
        question_lower = question.lower()
        
        # Answer specific questions about averages
        if 'average' in question_lower and 'price' in question_lower:
            if 'price' in numeric_analysis:
                avg = numeric_analysis['price']['average']
                min_val = numeric_analysis['price']['min']
                max_val = numeric_analysis['price']['max']
                return f"The **average price** in your dataset is **${avg:.2f}**. Prices range from ${min_val:.2f} to ${max_val:.2f}."
            else:
                return "I don't see a 'price' column in your data. Available columns are: " + ", ".join(headers)
        
        # Answer questions about highest/maximum values
        elif any(word in question_lower for word in ['highest', 'maximum', 'max']) and 'price' in question_lower:
            if 'price' in numeric_analysis:
                max_val = numeric_analysis['price']['max']
                return f"The **highest price** in your dataset is **${max_val:.2f}**."
            else:
                return "I don't see a 'price' column in your data. Available columns are: " + ", ".join(headers)
        
        # Answer questions about count/how many
        elif any(word in question_lower for word in ['how many', 'count', 'total']) and 'row' not in question_lower:
            return f"Your dataset contains **{len(data_rows)} records** with **{len(headers)} columns**: {', '.join(headers)}."
        
        # General analysis
        else:
            response_parts = [
                f"I've analyzed your CSV data with **{len(data_rows)} rows** and **{len(headers)} columns**."
            ]
            
            if numeric_analysis:
                response_parts.append("\n**Numeric columns found:**")
                for col, stats in numeric_analysis.items():
                    response_parts.append(f"• **{col}**: Average = {stats['average']:.2f}, Range = {stats['min']:.2f} to {stats['max']:.2f}")
            
            response_parts.append(f"\n**Columns available**: {', '.join(headers)}")
            response_parts.append("\nFeel free to ask specific questions about your data!")
            
            return "".join(response_parts)

def main():
    """Start the minimal backend server"""
    PORT = 8000
    
    print("🚀 Starting Horus AI-BI Minimal Backend Server")
    print("=" * 50)
    print(f"🌐 Server running on: http://localhost:{PORT}")
    print(f"🩺 Health check: http://localhost:{PORT}/health")
    print(f"💬 Chat API: http://localhost:{PORT}/api/v1/conversational/analyze")
    print("📚 This is a minimal backend that works without FastAPI")
    print("📝 Your frontend should now be able to connect!")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    with socketserver.TCPServer(("", PORT), HorusRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()