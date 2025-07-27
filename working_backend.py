#!/usr/bin/env python3

"""
Working Backend for Horus AI-BI Platform
Simple HTTP server that works without external dependencies
"""

import http.server
import socketserver
import json
import re

# Simple in-memory storage for conversations
CONVERSATIONS = {}

class WorkingHorusHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Override to reduce console noise"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/health':
            response = {
                "status": "healthy",
                "service": "Horus AI-BI Platform",
                "version": "1.0.0-working",
                "port": 8003,
                "message": "Backend is running and ready!"
            }
        else:
            response = {
                "message": "🤖 Horus AI-BI Backend is Running!",
                "status": "operational",
                "port": 8003,
                "endpoints": {
                    "health": "/health",
                    "chat": "/api/v1/conversational/analyze"
                }
            }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if '/conversational/analyze' in self.path:
            self.handle_chat_analyze()
        elif '/conversational/continue' in self.path:
            self.handle_chat_continue()
        else:
            self.send_error_response("Endpoint not found", 404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def handle_chat_analyze(self):
        """Handle initial chat with file upload"""
        try:
            # Read the request data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise Exception("No data received")
            
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            # Parse form data
            question = self.extract_form_field(post_data, 'question') or 'What can you tell me about this data?'
            user_id = self.extract_form_field(post_data, 'user_id') or 'anonymous'
            
            # Look for CSV data
            csv_data = self.extract_csv_from_upload(post_data)
            
            # Analyze the data
            if csv_data:
                analysis = self.analyze_csv_data(csv_data, question)
                answer = analysis['answer']
                data_summary = analysis['summary']
            else:
                answer = "🤖 Hello! I'm your Horus AI assistant. I don't see any CSV data in your upload. Please upload a CSV file and ask me questions like:\n\n• 'What is the average price?'\n• 'How many records do we have?'\n• 'What's the highest value?'\n\nI'll analyze your data and give you specific insights!"
                data_summary = {
                    "filename": "no_file",
                    "total_rows": 0,
                    "message": "Please upload a CSV file to get started"
                }
            
            # Generate conversation ID and store data
            conv_id = f"conv_{hash(user_id + question) % 100000}"
            
            # Store conversation data for follow-up questions
            if csv_data:
                CONVERSATIONS[conv_id] = {
                    "csv_data": csv_data,
                    "analysis": analysis,
                    "user_id": user_id,
                    "timestamp": "now"
                }
            
            # Generate response
            response = {
                "conversation_id": conv_id,
                "question": question,
                "answer": answer,
                "data_summary": data_summary,
                "visualization": {"type": "none", "message": "CSV analysis available"},
                "follow_up_questions": [
                    "What is the average of a numeric column?",
                    "How many rows are in the dataset?", 
                    "What are the column names?",
                    "Show me a summary of the data"
                ],
                "success": True
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(f"Chat analysis error: {str(e)}")
    
    def handle_chat_continue(self):
        """Handle follow-up chat messages"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            question = self.extract_form_field(post_data, 'question') or 'Follow-up question'
            conv_id = self.extract_form_field(post_data, 'conversation_id') or 'unknown'
            
            # Check if we have stored conversation data
            if conv_id in CONVERSATIONS:
                stored_data = CONVERSATIONS[conv_id]
                csv_data = stored_data['csv_data']
                
                # Re-analyze the data with the new question
                analysis = self.analyze_csv_data(csv_data, question)
                answer = analysis['answer']
            else:
                # Handle common follow-up questions intelligently when no stored data
                q = question.lower()
                
                if 'average' in q and ('price' in q or 'monthly_fee' in q or 'fee' in q):
                    answer = "🤖 I don't have access to your previous data in this session. Please re-upload your CSV file and I'll calculate the exact average price/fee for you!"
                elif 'how many' in q and ('user' in q or 'customer' in q or 'record' in q or 'row' in q):
                    answer = "🤖 I need access to your data to count users/customers. Please re-upload your CSV file and I'll give you the exact count!"
                elif 'postpaid' in q or 'prepaid' in q:
                    answer = "🤖 To count postpaid/prepaid users, I need to analyze your data. Please re-upload your CSV file and I'll filter and count the specific plan types for you!"
                else:
                    answer = f"🤖 I need access to your data to answer '{question}'. Please re-upload your CSV file and I'll give you detailed insights!"
            
            response = {
                "conversation_id": conv_id,
                "question": question,
                "answer": answer,
                "follow_up_questions": [
                    "Re-upload CSV for exact calculations",
                    "What specific column should I analyze?",
                    "Show me data patterns and insights",
                    "Calculate averages, totals, or maximums"
                ],
                "success": True
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(f"Continue chat error: {str(e)}")
    
    def extract_form_field(self, data, field_name):
        """Extract form field from multipart data"""
        pattern = f'name="{field_name}".*?\\r?\\n\\r?\\n(.*?)(?=\\r?\\n--|\\r?\\n$|$)'
        match = re.search(pattern, data, re.DOTALL)
        return match.group(1).strip() if match else None
    
    def extract_csv_from_upload(self, data):
        """Extract CSV content from file upload"""
        # Look for CSV content after filename
        if 'filename=' in data and '.csv' in data:
            # Try both types of line endings
            for separator in ['\r\n\r\n', '\\r\\n\\r\\n', '\n\n']:
                parts = data.split(separator)
                for part in parts:
                    if ',' in part and ('\n' in part or '\\n' in part) and len(part.strip()) > 30:
                        # Clean up the part - remove boundary markers and extra whitespace
                        clean_part = part.strip()
                        # Remove boundary markers if present
                        if clean_part.startswith('--'):
                            continue
                        # Check if it looks like CSV data
                        lines = clean_part.replace('\\n', '\n').split('\n')
                        lines = [line.strip() for line in lines if line.strip()]
                        if len(lines) >= 2 and ',' in lines[0]:
                            return '\n'.join(lines)
        return None
    
    def analyze_csv_data(self, csv_data, question):
        """Analyze CSV data and generate response"""
        try:
            # Handle both literal \n and actual newlines
            if '\\n' in csv_data:
                lines = [line.strip() for line in csv_data.split('\\n') if line.strip()]
            else:
                lines = [line.strip() for line in csv_data.split('\n') if line.strip()]
            
            if len(lines) < 2:
                raise Exception(f"Need header and data rows. Found {len(lines)} lines: {lines[:3]}")
            
            # Parse CSV
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
            answer = self.generate_data_answer(question, numeric_stats, data_rows, headers)
            
            return {
                'answer': answer,
                'summary': {
                    'filename': 'uploaded_data.csv',
                    'total_rows': len(data_rows),
                    'total_columns': len(headers),
                    'columns': headers,
                    'numeric_columns': list(numeric_stats.keys()),
                    'sample_data': data_rows[:3]
                }
            }
            
        except Exception as e:
            return {
                'answer': f"I had trouble analyzing your CSV data: {str(e)}. Please ensure it's properly formatted with headers and comma-separated values.",
                'summary': {'error': str(e)}
            }
    
    def generate_data_answer(self, question, numeric_stats, data_rows, headers):
        """Generate specific answer based on question and data"""
        q = question.lower()
        
        # Average price questions
        if 'average' in q and 'price' in q:
            if 'price' in numeric_stats:
                avg = numeric_stats['price']['average']
                return f"The **average price** in your dataset is **${avg:.2f}**. The price range is ${numeric_stats['price']['min']:.2f} to ${numeric_stats['price']['max']:.2f}."
            return f"No 'price' column found. Available columns: {', '.join(headers)}"
        
        # Specific count questions with filtering
        elif 'postpaid' in q and any(word in q for word in ['how many', 'count', 'user', 'customer']):
            postpaid_count = 0
            plan_column = None
            # Find the plan/contract type column
            for col in headers:
                if any(keyword in col.lower() for keyword in ['plan', 'contract', 'type', 'service']):
                    plan_column = col
                    break
            
            if plan_column:
                for row in data_rows:
                    plan_value = row.get(plan_column, '').lower()
                    if 'postpaid' in plan_value or 'post-paid' in plan_value or 'post paid' in plan_value:
                        postpaid_count += 1
                return f"Your dataset has **{postpaid_count} postpaid users** out of {len(data_rows)} total customers. (Found in '{plan_column}' column)"
            else:
                return f"I couldn't find a plan type column to filter postpaid users. Available columns: {', '.join(headers)}"
        
        # Prepaid count questions
        elif 'prepaid' in q and any(word in q for word in ['how many', 'count', 'user', 'customer']):
            prepaid_count = 0
            plan_column = None
            for col in headers:
                if any(keyword in col.lower() for keyword in ['plan', 'contract', 'type', 'service']):
                    plan_column = col
                    break
            
            if plan_column:
                for row in data_rows:
                    plan_value = row.get(plan_column, '').lower()
                    if 'prepaid' in plan_value or 'pre-paid' in plan_value or 'pre paid' in plan_value:
                        prepaid_count += 1
                return f"Your dataset has **{prepaid_count} prepaid users** out of {len(data_rows)} total customers. (Found in '{plan_column}' column)"
            else:
                return f"I couldn't find a plan type column to filter prepaid users. Available columns: {', '.join(headers)}"
        
        # General count questions
        elif any(word in q for word in ['how many', 'count', 'total']) and 'row' not in q:
            return f"Your dataset has **{len(data_rows)} records** with **{len(headers)} columns**: {', '.join(headers)}"
        
        # Highest/maximum questions
        elif any(word in q for word in ['highest', 'maximum', 'max']):
            if 'price' in q and 'price' in numeric_stats:
                return f"The **highest price** is **${numeric_stats['price']['max']:.2f}**"
            elif numeric_stats:
                col = list(numeric_stats.keys())[0]
                return f"The **highest {col}** is **{numeric_stats[col]['max']:.2f}**"
            return "Please specify which column you want the maximum for."
        
        # General data overview
        else:
            parts = [f"🔍 **Data Analysis Results:**\\n\\nYour CSV has **{len(data_rows)} rows** and **{len(headers)} columns**."]
            
            if numeric_stats:
                parts.append("\\n**📊 Numeric Analysis:**")
                for col, stats in list(numeric_stats.items())[:3]:  # Show top 3
                    parts.append(f"• **{col}**: avg={stats['average']:.2f}, range={stats['min']:.2f}-{stats['max']:.2f}")
            
            parts.append(f"\\n**📋 Available columns:** {', '.join(headers)}")
            parts.append("\\n**💡 Try asking:** 'What is the average price?' or 'How many records?'")
            
            return "".join(parts)
    
    def send_json_response(self, data):
        """Send JSON response with CORS"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_error_response(self, message, code=500):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"error": message, "success": False}
        self.wfile.write(json.dumps(response).encode())

def main():
    PORT = 8004
    
    print("🚀 HORUS AI-BI WORKING BACKEND")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:{PORT}")
    print(f"🩺 Health: http://localhost:{PORT}/health")
    print(f"💬 Chat: http://localhost:{PORT}/api/v1/conversational/analyze")
    print()
    print("✅ No dependencies required!")
    print("✅ CORS enabled for frontend")
    print("✅ CSV upload and analysis supported")
    print("✅ Ready for your React frontend!")
    print()
    print("🎯 Your NetworkError should be completely fixed!")
    print("📝 Test: curl http://localhost:8003/health")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), WorkingHorusHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\\n❌ Server error: {e}")

if __name__ == "__main__":
    main()