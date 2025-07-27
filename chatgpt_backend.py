#!/usr/bin/env python3

"""
ChatGPT-Like Data Analysis Backend
Persistent conversation memory with full data context
"""

import http.server
import socketserver
import json
import re
import hashlib
from datetime import datetime

# Persistent conversation memory (like ChatGPT)
CONVERSATIONS = {}

class ChatGPTLikeHandler(http.server.BaseHTTPRequestHandler):
    
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
                "service": "Horus AI-BI Platform (ChatGPT-like)",
                "version": "2.0.0-chatgpt",
                "port": 8005,
                "memory_active": len(CONVERSATIONS),
                "message": "ChatGPT-like data analysis ready!"
            }
        else:
            response = {
                "message": "🤖 Horus AI-BI Platform (ChatGPT-like)",
                "status": "operational",
                "active_conversations": len(CONVERSATIONS),
                "endpoints": {
                    "health": "/health",
                    "chat": "/api/v1/conversational/analyze",
                    "continue": "/api/v1/conversational/continue"
                }
            }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if '/conversational/analyze' in self.path:
            self.handle_initial_analysis()
        elif '/conversational/continue' in self.path:
            self.handle_continue_conversation()
        else:
            self.send_error_response("Endpoint not found", 404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def handle_initial_analysis(self):
        """Handle initial CSV upload and analysis"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise Exception("No data received")
            
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            # Parse form data
            question = self.extract_form_field(post_data, 'question') or 'Analyze this data'
            user_id = self.extract_form_field(post_data, 'user_id') or 'anonymous'
            
            # Extract CSV data
            csv_data = self.extract_csv_from_upload(post_data)
            
            # Create conversation ID
            conv_id = f"conv_{hashlib.md5((user_id + str(datetime.now())).encode()).hexdigest()[:8]}"
            
            if csv_data:
                # Parse and analyze the data
                parsed_data = self.parse_csv_data(csv_data)
                analysis_result = self.analyze_question(question, parsed_data)
                
                # Store EVERYTHING in conversation memory (like ChatGPT)
                CONVERSATIONS[conv_id] = {
                    "user_id": user_id,
                    "csv_data": csv_data,
                    "parsed_data": parsed_data,
                    "conversation_history": [
                        {"role": "user", "content": question, "timestamp": datetime.now().isoformat()},
                        {"role": "assistant", "content": analysis_result["answer"], "timestamp": datetime.now().isoformat()}
                    ],
                    "data_context": {
                        "filename": "user_data.csv",
                        "total_rows": len(parsed_data["data_rows"]),
                        "total_columns": len(parsed_data["headers"]),
                        "columns": parsed_data["headers"],
                        "numeric_columns": list(parsed_data["numeric_stats"].keys()),
                        "sample_data": parsed_data["data_rows"][:3]
                    },
                    "created_at": datetime.now().isoformat()
                }
                
                response = {
                    "conversation_id": conv_id,
                    "question": question,
                    "answer": analysis_result["answer"],
                    "data_summary": CONVERSATIONS[conv_id]["data_context"],
                    "visualization": {"type": "table", "data": parsed_data["data_rows"][:5]},
                    "follow_up_questions": [
                        "How many postpaid users do we have?",
                        "What's the average monthly fee?",
                        "Show me the highest spenders",
                        "Which city has the most customers?"
                    ],
                    "success": True
                }
            else:
                response = {
                    "conversation_id": conv_id,
                    "question": question,
                    "answer": "🤖 I don't see any CSV data. Please upload a CSV file and I'll analyze it for you!",
                    "success": False
                }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(f"Analysis error: {str(e)}")
    
    def handle_continue_conversation(self):
        """Handle follow-up questions with FULL memory access"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
            
            question = self.extract_form_field(post_data, 'question') or 'Follow-up question'
            conv_id = self.extract_form_field(post_data, 'conversation_id') or 'unknown'
            
            if conv_id in CONVERSATIONS:
                # Get the stored conversation data
                conversation = CONVERSATIONS[conv_id]
                parsed_data = conversation["parsed_data"]
                
                # Analyze the new question with full data access
                analysis_result = self.analyze_question(question, parsed_data)
                
                # Add to conversation history (like ChatGPT)
                conversation["conversation_history"].extend([
                    {"role": "user", "content": question, "timestamp": datetime.now().isoformat()},
                    {"role": "assistant", "content": analysis_result["answer"], "timestamp": datetime.now().isoformat()}
                ])
                
                response = {
                    "conversation_id": conv_id,
                    "question": question,
                    "answer": analysis_result["answer"],
                    "data_summary": conversation["data_context"],
                    "conversation_history": conversation["conversation_history"][-4:],  # Last 2 exchanges
                    "follow_up_questions": [
                        "Tell me more about this data",
                        "What other insights can you find?",
                        "Show me different analysis",
                        "Compare different segments"
                    ],
                    "success": True
                }
            else:
                response = {
                    "conversation_id": conv_id,
                    "question": question,
                    "answer": "🤖 I don't have the conversation history. Please start a new conversation by uploading your CSV file.",
                    "success": False
                }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(f"Continue conversation error: {str(e)}")
    
    def extract_form_field(self, data, field_name):
        """Extract form field from multipart data"""
        pattern = f'name="{field_name}".*?\\r?\\n\\r?\\n(.*?)(?=\\r?\\n--|\\r?\\n$|$)'
        match = re.search(pattern, data, re.DOTALL)
        return match.group(1).strip() if match else None
    
    def extract_csv_from_upload(self, data):
        """Extract CSV content from file upload"""
        if 'filename=' in data and '.csv' in data:
            for separator in ['\r\n\r\n', '\\r\\n\\r\\n', '\n\n']:
                parts = data.split(separator)
                for part in parts:
                    if ',' in part and ('\n' in part or '\\n' in part) and len(part.strip()) > 30:
                        clean_part = part.strip()
                        if clean_part.startswith('--'):
                            continue
                        lines = clean_part.replace('\\n', '\n').split('\n')
                        lines = [line.strip() for line in lines if line.strip()]
                        if len(lines) >= 2 and ',' in lines[0]:
                            return '\n'.join(lines)
        return None
    
    def parse_csv_data(self, csv_data):
        """Parse CSV data into structured format"""
        lines = [line.strip() for line in csv_data.split('\n') if line.strip()]
        
        headers = [h.strip().strip('"') for h in lines[0].split(',')]
        data_rows = []
        
        for line in lines[1:]:
            row = [cell.strip().strip('"') for cell in line.split(',')]
            if len(row) == len(headers):
                data_rows.append(dict(zip(headers, row)))
        
        # Calculate numeric statistics
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
                    'max': max(values),
                    'sum': sum(values)
                }
        
        return {
            "headers": headers,
            "data_rows": data_rows,
            "numeric_stats": numeric_stats
        }
    
    def analyze_question(self, question, parsed_data):
        """Analyze question and generate intelligent response"""
        q = question.lower()
        headers = parsed_data["headers"]
        data_rows = parsed_data["data_rows"]
        numeric_stats = parsed_data["numeric_stats"]
        
        # Postpaid users
        if 'postpaid' in q and any(word in q for word in ['how many', 'count', 'user', 'customer']):
            postpaid_count = 0
            plan_column = self.find_column(headers, ['plan', 'contract', 'type'])
            
            if plan_column:
                for row in data_rows:
                    plan_value = row.get(plan_column, '').lower()
                    if 'postpaid' in plan_value:
                        postpaid_count += 1
                return {"answer": f"You have **{postpaid_count} postpaid users** out of {len(data_rows)} total customers."}
            else:
                return {"answer": f"I couldn't find a plan type column. Available columns: {', '.join(headers)}"}
        
        # Prepaid users
        elif 'prepaid' in q and any(word in q for word in ['how many', 'count', 'user', 'customer']):
            prepaid_count = 0
            plan_column = self.find_column(headers, ['plan', 'contract', 'type'])
            
            if plan_column:
                for row in data_rows:
                    plan_value = row.get(plan_column, '').lower()
                    if 'prepaid' in plan_value:
                        prepaid_count += 1
                return {"answer": f"You have **{prepaid_count} prepaid users** out of {len(data_rows)} total customers."}
            else:
                return {"answer": f"I couldn't find a plan type column. Available columns: {', '.join(headers)}"}
        
        # Average price/fee
        elif 'average' in q and ('price' in q or 'fee' in q or 'monthly' in q):
            fee_column = self.find_column(headers, ['fee', 'price', 'monthly', 'cost'])
            if fee_column and fee_column in numeric_stats:
                avg = numeric_stats[fee_column]['average']
                return {"answer": f"The **average {fee_column.lower()}** is **${avg:.2f}** (range: ${numeric_stats[fee_column]['min']:.2f} - ${numeric_stats[fee_column]['max']:.2f})"}
            else:
                return {"answer": f"No fee/price column found. Available columns: {', '.join(headers)}"}
        
        # General count
        elif 'how many' in q and any(word in q for word in ['user', 'customer', 'record', 'row']):
            return {"answer": f"You have **{len(data_rows)} total customers/users** in your dataset with **{len(headers)} data fields**."}
        
        # Highest values
        elif any(word in q for word in ['highest', 'maximum', 'max', 'top']):
            if numeric_stats:
                # Find most relevant numeric column
                for col_name, stats in numeric_stats.items():
                    if any(keyword in col_name.lower() for keyword in ['fee', 'price', 'spend', 'usage']):
                        return {"answer": f"The **highest {col_name.lower()}** is **{stats['max']:.2f}** (average: {stats['average']:.2f})"}
                
                # Default to first numeric column
                col_name = list(numeric_stats.keys())[0]
                stats = numeric_stats[col_name]
                return {"answer": f"The **highest {col_name.lower()}** is **{stats['max']:.2f}**"}
            else:
                return {"answer": f"No numeric columns found for maximum calculation. Available columns: {', '.join(headers)}"}
        
        # Default analysis
        else:
            summary_parts = [f"📊 **Dataset Overview:** {len(data_rows)} customers with {len(headers)} data fields"]
            
            if numeric_stats:
                summary_parts.append("\\n**Key Statistics:**")
                for col, stats in list(numeric_stats.items())[:3]:
                    summary_parts.append(f"• **{col}**: avg={stats['average']:.2f}, max={stats['max']:.2f}")
            
            summary_parts.append(f"\\n**Available data:** {', '.join(headers)}")
            summary_parts.append("\\n**Ask me anything!** Like 'How many postpaid users?' or 'What's the average fee?'")
            
            return {"answer": "".join(summary_parts)}
    
    def find_column(self, headers, keywords):
        """Find column name containing any of the keywords"""
        for header in headers:
            if any(keyword in header.lower() for keyword in keywords):
                return header
        return None
    
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
    PORT = 8005
    
    print("🚀 HORUS AI-BI CHATGPT-LIKE BACKEND")
    print("=" * 60)
    print(f"🌐 Server: http://localhost:{PORT}")
    print(f"🩺 Health: http://localhost:{PORT}/health")
    print(f"💬 Chat: http://localhost:{PORT}/api/v1/conversational/analyze")
    print(f"🔄 Continue: http://localhost:{PORT}/api/v1/conversational/continue")
    print()
    print("✅ ChatGPT-like conversation memory")
    print("✅ Persistent data storage throughout conversation")
    print("✅ NO re-upload requests")
    print("✅ Intelligent follow-up question handling")
    print("✅ Full data context in every response")
    print()
    print("🎯 True ChatGPT experience for data analysis!")
    print("📝 Test: Ask 'How many postpaid users?' after uploading CSV")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), ChatGPTLikeHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\\n❌ Server error: {e}")

if __name__ == "__main__":
    main()