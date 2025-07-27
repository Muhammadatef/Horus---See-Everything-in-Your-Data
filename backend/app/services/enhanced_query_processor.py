"""
Enhanced Query Processor with Real-time Updates and Smart Visualization
Combines LLM, SQL generation, and visualization in a seamless workflow
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.enhanced_llm_service import EnhancedLLMService
from app.services.visualization_engine import visualization_engine
from app.services.websocket_manager import websocket_manager
from app.database import Dataset, DataSource

logger = logging.getLogger(__name__)


class EnhancedQueryProcessor:
    """Enhanced query processor with real-time updates and intelligent visualization"""
    
    def __init__(self):
        self.llm_service = EnhancedLLMService()
    
    async def _analyze_user_intent(self, question: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user intent to determine response type"""
        
        question_lower = question.lower().strip()
        
        # Check for data analysis keywords
        data_keywords = [
            'how many', 'count', 'total', 'sum', 'average', 'mean', 'median',
            'show me', 'display', 'visualize', 'chart', 'graph', 'plot',
            'compare', 'analyze', 'breakdown', 'distribution', 'pattern',
            'trend', 'correlation', 'statistics', 'min', 'max', 'top', 'bottom'
        ]
        
        visualization_keywords = [
            'show', 'display', 'visualize', 'chart', 'graph', 'plot', 
            'breakdown', 'distribution', 'compare'
        ]
        
        # Determine if this requires SQL execution
        requires_sql = any(keyword in question_lower for keyword in data_keywords)
        
        # Determine visualization type
        visualization_type = None
        if any(keyword in question_lower for keyword in visualization_keywords):
            if any(word in question_lower for word in ['compare', 'vs', 'breakdown', 'distribution']):
                visualization_type = 'bar_chart'
            elif any(word in question_lower for word in ['trend', 'over time', 'timeline']):
                visualization_type = 'line_chart' 
            elif any(word in question_lower for word in ['total', 'sum', 'count', 'how many']):
                visualization_type = 'kpi'
            else:
                visualization_type = 'table'
        
        # Determine primary intent
        primary_intent = 'exploration'
        if any(word in question_lower for word in ['how many', 'count', 'total']):
            primary_intent = 'metrics'
        elif any(word in question_lower for word in ['compare', 'vs', 'versus']):
            primary_intent = 'comparisons'
        elif any(word in question_lower for word in ['top', 'best', 'worst', 'highest', 'lowest']):
            primary_intent = 'rankings'
        elif any(word in question_lower for word in ['trend', 'over time', 'growth']):
            primary_intent = 'trends'
        
        return {
            'requires_sql': requires_sql,
            'visualization_type': visualization_type,
            'is_conversational': not requires_sql,
            'intent_keywords': [kw for kw in data_keywords if kw in question_lower],
            'complexity': 'simple' if len([kw for kw in data_keywords if kw in question_lower]) <= 2 else 'complex',
            'primary_intent': primary_intent,
            'confidence': 0.8,
            'entities': {'columns': [], 'aggregations': [], 'filters': []},
            'result_type': 'data_table',
            'time_dimension': None
        }
    
    async def _generate_sql_query(self, question: str, schema: Dict[str, Any], columns: List[str]) -> str:
        """Generate SQL query for the question"""
        
        # Use existing LLM service to generate SQL
        table_name = "temp_data_table"  # This would be dynamic in production
        
        # Create a simple intent analysis for SQL generation
        intent_analysis = await self._analyze_user_intent(question, schema)
        
        return await self.llm_service._generate_business_sql(
            question=question,
            schema=schema,
            table_name=table_name,
            intent_analysis=intent_analysis
        )
    
    async def process_query_with_updates(
        self,
        question: str,
        dataset_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process natural language query with real-time status updates"""
        
        query_id = str(uuid.uuid4())
        
        try:
            # Check if this is a conversational message rather than a data query
            if self._is_conversational_message(question):
                conversational_response = self._handle_conversational_message(question)
                
                await websocket_manager.send_query_update(
                    user_id=user_id,
                    query_id=query_id,
                    status="completed",
                    progress=100,
                    message="✅ Conversational response generated!",
                    results={"question": question, "answer": conversational_response}
                )
                
                return {
                    "success": True,
                    "question": question,
                    "answer": conversational_response,
                    "sql": None,
                    "results": None,
                    "visualization": None,
                    "metadata": {
                        "query_type": "conversational",
                        "execution_summary": "Conversational response - no data analysis needed"
                    }
                }
            
            # Send initial query processing update
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="analyzing",
                progress=10,
                message="🤔 Understanding your question...",
                results={"question": question}
            )
            
            # Get dataset information
            dataset = await db.get(Dataset, uuid.UUID(dataset_id))
            if not dataset:
                raise ValueError("Dataset not found")
            
            # Get data source for schema information
            data_source = await db.get(DataSource, dataset.data_source_id)
            if not data_source:
                raise ValueError("Data source not found")
            
            schema_raw = data_source.schema_info or {}
            
            # Handle different schema formats
            if isinstance(schema_raw, dict) and "columns" in schema_raw:
                # If schema is in format {"columns": [...]} convert to proper format
                schema = {}
                for col in schema_raw["columns"]:
                    if isinstance(col, str):
                        # Simple column name, create basic schema entry
                        schema[col] = {"type": "text", "description": f"{col} column"}
                    elif isinstance(col, dict):
                        # Column with metadata
                        col_name = col.get("name", col.get("column", "unknown"))
                        schema[col_name] = col
            else:
                # Assume it's already in the correct format
                schema = schema_raw
            table_name = dataset.table_name
            
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="generating_sql",
                progress=30,
                message="⚡ Generating SQL query...",
                results={"dataset": dataset.display_name}
            )
            
            # Step 1: Generate SQL using Enhanced LLM
            business_analysis = await self.llm_service.analyze_business_question(
                question=question,
                schema=schema,
                table_name=table_name
            )
            sql_query = business_analysis["sql"]
            
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="executing",
                progress=50,
                message="🔍 Executing query on your data...",
                results={"sql": sql_query}
            )
            
            # Step 2: Execute SQL query
            query_results = await self._execute_sql_query(sql_query, db)
            
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="analyzing_results",
                progress=70,
                message="📊 Analyzing results and preparing visualization...",
                results={
                    "row_count": len(query_results.get("data", [])),
                    "columns": query_results.get("columns", [])
                }
            )
            
            # Step 3: Generate natural language answer - Universal approach
            answer = await self.llm_service.generate_business_answer(
                question=question,
                results=query_results,
                schema=schema,
                intent_analysis=business_analysis["intent"]
            )
            
            # Step 4: Determine query intent for visualization
            intent_type = self._analyze_query_intent(question)
            
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="creating_visualization",
                progress=85,
                message="🎨 Creating intelligent visualization...",
                results={"intent": intent_type, "answer": answer}
            )
            
            # Step 5: Generate visualization
            visualization = await visualization_engine.generate_visualization(
                data=query_results.get("data", []),
                columns=query_results.get("columns", []),
                question=question,
                schema=schema,
                intent_type=intent_type
            )
            
            # Final result
            final_result = {
                "success": True,
                "question": question,
                "answer": answer,
                "sql": sql_query,
                "results": query_results,
                "visualization": visualization,
                "metadata": {
                    "dataset_name": dataset.display_name,
                    "query_intent": intent_type,
                    "execution_summary": self._generate_execution_summary(query_results, visualization)
                }
            }
            
            # Send completion update
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="completed",
                progress=100,
                message="✅ Query completed successfully!",
                results=final_result
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            
            # Send error update
            await websocket_manager.send_query_update(
                user_id=user_id,
                query_id=query_id,
                status="failed",
                progress=0,
                message=f"❌ Query failed: {str(e)}",
                results={"error": str(e)}
            )
            
            return {
                "success": False,
                "question": question,
                "error": str(e),
                "answer": f"I'm sorry, I couldn't process your question: {str(e)}"
            }
    
    async def _execute_sql_query(self, sql: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute SQL query and return structured results"""
        
        try:
            # Execute the query
            result = await db.execute(text(sql))
            
            # Fetch results
            rows = result.fetchall()
            
            if not rows:
                return {
                    "data": [],
                    "columns": [],
                    "row_count": 0
                }
            
            # Get column names
            columns = list(result.keys())
            
            # Convert rows to dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Handle special types for JSON serialization
                    if hasattr(value, 'isoformat'):  # datetime
                        value = value.isoformat()
                    elif hasattr(value, '__float__'):  # decimal
                        value = float(value)
                    row_dict[col] = value
                data.append(row_dict)
            
            return {
                "data": data,
                "columns": columns,
                "row_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise Exception(f"Database query failed: {str(e)}")
    
    def _analyze_query_intent(self, question: str) -> str:
        """Analyze the intent of the natural language question"""
        
        question_lower = question.lower()
        
        # Count/aggregation questions
        if any(word in question_lower for word in ['how many', 'count', 'number of', 'total']):
            return "count"
        
        # Comparison questions
        if any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference', 'between']):
            return "comparison"
        
        # Trend/time-based questions
        if any(word in question_lower for word in ['trend', 'over time', 'timeline', 'historical', 'change']):
            return "trend"
        
        # Distribution questions
        if any(word in question_lower for word in ['distribution', 'breakdown', 'spread', 'pattern']):
            return "distribution"
        
        # Ranking questions
        if any(word in question_lower for word in ['top', 'bottom', 'highest', 'lowest', 'best', 'worst']):
            return "ranking"
        
        # Aggregation questions (average, sum, etc.)
        if any(word in question_lower for word in ['average', 'avg', 'mean', 'sum', 'total', 'maximum', 'minimum']):
            return "aggregation"
        
        # Filter/search questions
        if any(word in question_lower for word in ['show', 'find', 'get', 'list', 'where', 'which']):
            return "filter"
        
        return "general"
    
    def _generate_execution_summary(self, query_results: Dict[str, Any], visualization: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution summary for the query"""
        
        return {
            "rows_returned": query_results.get("row_count", 0),
            "columns_returned": len(query_results.get("columns", [])),
            "visualization_type": visualization.get("type", "unknown"),
            "has_insights": len(visualization.get("insights", [])) > 0,
            "recommended_actions": visualization.get("data_summary", {}).get("recommended_actions", [])
        }
    
    async def get_intelligent_suggestions(
        self,
        dataset_id: str,
        partial_question: str,
        db: AsyncSession
    ) -> List[str]:
        """Generate intelligent query suggestions based on dataset and partial question"""
        
        try:
            # Get dataset information
            dataset = await db.get(Dataset, uuid.UUID(dataset_id))
            if not dataset:
                return []
            
            # Get sample questions from dataset
            base_suggestions = dataset.sample_questions or []
            
            # If partial question provided, filter and enhance suggestions
            if partial_question:
                partial_lower = partial_question.lower()
                
                # Filter relevant suggestions
                relevant_suggestions = [
                    suggestion for suggestion in base_suggestions
                    if any(word in suggestion.lower() for word in partial_lower.split())
                ]
                
                # Add context-aware suggestions
                contextual_suggestions = self._generate_contextual_suggestions(partial_question, dataset)
                
                return relevant_suggestions[:5] + contextual_suggestions[:3]
            
            return base_suggestions[:8]
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return []
    
    def _generate_contextual_suggestions(self, partial_question: str, dataset: Dataset) -> List[str]:
        """Generate contextual suggestions based on partial question"""
        
        suggestions = []
        partial_lower = partial_question.lower()
        dataset_name = dataset.display_name.lower()
        
        # Question starters based on common patterns
        if partial_lower.startswith(('how many', 'count')):
            suggestions.extend([
                f"How many records are in {dataset.display_name}?",
                f"How many unique values are there?",
                f"Count by category or status"
            ])
        
        elif partial_lower.startswith(('what is', 'what are')):
            suggestions.extend([
                f"What is the average value?",
                f"What are the top categories?",
                f"What is the distribution?"
            ])
        
        elif partial_lower.startswith(('show me', 'show')):
            suggestions.extend([
                f"Show me trends over time",
                f"Show me the breakdown by category",
                f"Show me the top 10 records"
            ])
        
        elif 'trend' in partial_lower:
            suggestions.extend([
                f"Show trends over time",
                f"What are the historical patterns?",
                f"How has this changed over time?"
            ])
        
        return suggestions
    
    def _is_conversational_message(self, question: str) -> bool:
        """Intelligently detect if the message is conversational vs data analysis request"""
        
        question_lower = question.lower().strip()
        
        # 1. Clear conversational patterns (always conversational)
        conversational_patterns = [
            # Greetings
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings',
            # Pleasantries
            'thank you', 'thanks', 'goodbye', 'bye', 'see you', 'nice to meet',
            # About/Help requests
            'help', 'what can you do', 'how do you work', 'what are your capabilities',
            'who are you', 'what are you', 'tell me about yourself', 'introduce yourself',
            # Casual conversation
            'how are you', 'nice to meet you', 'good job', 'well done', 'amazing', 'awesome'
        ]
        
        for pattern in conversational_patterns:
            if pattern in question_lower:
                return True
        
        # 2. Data analysis indicators (never conversational)
        data_indicators = [
            # Query words
            'show', 'display', 'list', 'find', 'get', 'retrieve', 'fetch',
            # Analysis terms
            'analyze', 'analysis', 'calculate', 'count', 'sum', 'average', 'total',
            # Data terms
            'data', 'records', 'rows', 'table', 'database', 'dataset', 'information',
            # Question starters for data
            'how many', 'what is', 'what are', 'which', 'when', 'where',
            # Business terms
            'users', 'customers', 'sales', 'revenue', 'profit', 'orders', 'products',
            'active', 'inactive', 'status', 'region', 'country', 'spending',
            # Comparative terms
            'compare', 'comparison', 'versus', 'vs', 'between', 'difference',
            # Trend terms
            'trend', 'over time', 'historical', 'growth', 'decline', 'change',
            # Visualization requests
            'chart', 'graph', 'visualization', 'plot', 'dashboard', 'report'
        ]
        
        # IMPORTANT: Check for data indicators FIRST and make it definitive
        # These should NEVER be treated as conversational
        for indicator in data_indicators:
            if indicator in question_lower:
                return False
        
        # 3. Question structure analysis - definitive data query patterns
        query_starters = [
            'how many', 'how much', 'what is the', 'what are the', 'show me',
            'give me', 'i want', 'i need', 'can you show', 'can you tell me about',
            'what about', 'tell me about the', 'analyze', 'calculate'
        ]
        
        for starter in query_starters:
            if question_lower.startswith(starter):
                # But still check if it's about general info rather than data
                general_info_terms = ['yourself', 'your capabilities', 'how you work', 'what you do']
                if any(term in question_lower for term in general_info_terms):
                    return True
                return False
        
        # 4. Strong business/data context indicators (should override length)
        has_business_context = any(term in question_lower for term in [
            'business', 'company', 'organization', 'metrics', 'kpi', 'dashboard',
            'insight', 'analytics', 'intelligence'
        ])
        
        if has_business_context:
            return False
        
        # 5. Length and complexity heuristics (but only for truly ambiguous cases)
        # Very short messages are usually conversational
        if len(question_lower) <= 3:
            return True
        
        # Single words that could be either
        single_word_conversational = ['ok', 'okay', 'yes', 'no', 'sure', 'great', 'cool', 'nice']
        if question_lower in single_word_conversational:
            return True
        
        # 6. REMOVED the problematic short message rule that was overriding data queries
        # OLD: if len(question_lower.split()) <= 4: return True
        # This was incorrectly treating "how many customers" as conversational
        
        # Default to data analysis if we can't determine (better to err on analysis side)
        return False
    
    def _handle_conversational_message(self, question: str) -> str:
        """Generate appropriate conversational responses like ChatGPT/Claude for Data Analysis"""
        
        question_lower = question.lower().strip()
        
        # Greetings
        if any(word in question_lower for word in ['hi', 'hello', 'hey']):
            return """👋 **Hello! I'm your Data Analysis Assistant**

Think of me as your personal data scientist who speaks plain English! I'm designed to help you understand your data through conversation, just like ChatGPT but specialized for data analysis.

🔍 **What makes me different:**
• **I explain, don't just calculate** - I'll tell you what your numbers mean for your business
• **I'm educational** - I'll help you understand statistical concepts as we go
• **I'm adaptive** - I adjust my analysis style based on what you need
• **I'm practical** - I focus on insights that help you make better decisions

📊 **My analysis capabilities:**
• **Statistical Analysis:** Averages, medians, distributions, correlations
• **Smart Visualizations:** Auto-generate the right charts for your questions  
• **Business Intelligence:** Turn data into actionable insights
• **Educational Explanations:** Learn data concepts as we explore together

💬 **How to work with me:**
Just talk to me naturally! Ask questions like:
• "What patterns do you see in my sales data?"
• "Help me understand my customer segments"
• "What should I focus on to grow my business?"

**Ready to turn your data into insights?** Upload your data or ask me anything! 📈"""

        # Good morning/afternoon/evening
        if any(time in question_lower for time in ['good morning', 'good afternoon', 'good evening']):
            return """🌅 **Good day! Ready to unlock insights from your data?**

I'm Horus, your dedicated AI Business Intelligence assistant. I'm here to transform your raw data into actionable business intelligence.

**What would you like to explore today?**
• Upload a dataset and ask questions
• Analyze trends, patterns, and metrics
• Generate visualizations and KPIs
• Get business recommendations

Let's turn your data into wisdom! 📊✨"""

        # Thank you
        if any(word in question_lower for word in ['thank', 'thanks']):
            return """🙏 **You're very welcome!**

I'm always happy to help you discover insights in your data. Data analysis is my passion!

**Need anything else?**
• More analysis on your current dataset?
• Want to explore different questions?
• Ready to upload new data?

I'm here whenever you need business intelligence! 𓂀"""

        # Help requests
        if any(word in question_lower for word in ['help', 'capabilities', 'what can you do']):
            return """🚀 **Data Analysis Assistant - Your AI Data Scientist**

I'm designed to be like ChatGPT, but specialized for data analysis and statistics. I combine the conversational abilities you love with deep data expertise.

**🧠 How I Analyze Data:**
• **Statistical Analysis:** I calculate means, medians, distributions, and correlations while explaining what they mean
• **Pattern Recognition:** I identify trends, outliers, and relationships in your data
• **Visual Intelligence:** I automatically choose the right charts and explain what they show
• **Business Context:** I translate numbers into business insights and recommendations

**📊 Data I Can Work With:**
• **File Formats:** CSV, Excel, JSON, Parquet
• **Data Types:** Sales data, customer data, financial data, survey responses, website analytics
• **Any Size:** From small datasets to large business databases

**💬 My Communication Style:**
• **Conversational:** Talk to me like you would a human analyst
• **Educational:** I explain concepts so you learn as we go
• **Adaptive:** I adjust my detail level based on your expertise
• **Practical:** I focus on actionable insights, not just numbers

**🎯 Example Conversations:**
• "Help me understand what's driving customer churn"
• "What story does my sales data tell?"
• "I need to present to my boss - what insights should I highlight?"
• "Explain this correlation to me like I'm not a statistician"

**Ready to explore your data together?** 📈✨"""

        # About questions
        if any(word in question_lower for word in ['who are you', 'what are you', 'about yourself']):
            return """🤖 **I'm your AI Data Analysis Assistant**

Think of me as ChatGPT's data-savvy cousin! I have the same conversational abilities you love, but I'm specifically trained to help you understand and analyze data.

**🎯 My Purpose:**
I bridge the gap between complex data analysis and human understanding. I take your data questions and turn them into insights you can actually use.

**🧠 What Makes Me Special:**
• **Conversational by Design:** No need to learn SQL or statistical jargon - just ask me questions naturally
• **Educational Approach:** I don't just give you numbers, I explain what they mean and why they matter
• **Adaptive Intelligence:** I adjust my explanations based on your level of data expertise
• **Business Focused:** I always try to connect statistical findings to real business implications

**🔍 My Analysis Philosophy:**
• Every dataset tells a story - I help you discover it
• Statistics should serve business decisions, not confuse them
• The best insights come from asking the right questions
• Data is only valuable when it leads to action

**💡 How I Work:**
Just like chatting with a knowledgeable colleague who happens to be really good with data. Ask me anything, and I'll help you find answers while teaching you about data analysis along the way.

**Ready to explore your data together?** 📊"""

        # Goodbye
        if any(word in question_lower for word in ['bye', 'goodbye', 'see you']):
            return """👋 **Farewell for now!**

Thank you for letting me help you explore your data today. Remember, I'm always here whenever you need business intelligence insights.

**Until next time:**
• Your data will be safely stored
• I'll be ready for more analysis
• Come back anytime with new questions

May your data bring you wisdom and success! 𓂀✨

*Horus - Your AI Business Intelligence Guardian*"""

        # Default conversational response
        return """💭 **I'm happy to chat!**

I can have conversations just like ChatGPT, but I really shine when we're exploring data together. I'm designed to make data analysis feel like a natural conversation.

**How about we dive into some data analysis?**
• **Upload your data** and I'll tell you what story it's telling
• **Ask me questions** about any dataset you have
• **Get explanations** of statistical concepts as we go
• **Discover insights** you might have missed

Think of me as your analytical thinking partner - I'm here to help you understand your data and make better decisions!

**What data questions are on your mind?** 🤔📊"""


# Global instance
enhanced_query_processor = EnhancedQueryProcessor()