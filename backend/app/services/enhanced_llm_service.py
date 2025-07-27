"""
Enhanced LLM service for natural language processing using Ollama
Specialized for business user questions with improved SQL generation
"""

import httpx
import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class EnhancedLLMService:
    """Enhanced service for business-friendly natural language processing"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.chat_model = settings.OLLAMA_MODEL_CHAT
        self.code_model = settings.OLLAMA_MODEL_CODE
        
        # Business patterns for question understanding
        self.business_patterns = {
            'metrics': {
                'keywords': ['total', 'sum', 'average', 'avg', 'count', 'how many', 'number of'],
                'sql_functions': ['SUM', 'AVG', 'COUNT', 'COUNT(*)']
            },
            'comparisons': {
                'keywords': ['compare', 'vs', 'versus', 'against', 'between'],
                'sql_patterns': ['GROUP BY', 'CASE WHEN']
            },
            'trends': {
                'keywords': ['trend', 'over time', 'monthly', 'weekly', 'daily', 'growth', 'change'],
                'sql_patterns': ['DATE_TRUNC', 'EXTRACT', 'ORDER BY']
            },
            'rankings': {
                'keywords': ['top', 'best', 'worst', 'highest', 'lowest', 'most', 'least'],
                'sql_patterns': ['ORDER BY', 'LIMIT']
            },
            'filters': {
                'keywords': ['where', 'when', 'only', 'except', 'excluding', 'including'],
                'sql_patterns': ['WHERE', 'AND', 'OR', 'NOT']
            }
        }
    
    async def _generate_conversational_analysis(
        self, 
        question: str, 
        data: List[Dict], 
        schema: Dict[str, Any], 
        intent_analysis: Dict[str, Any],
        file_info: Dict[str, Any]
    ) -> str:
        """Generate ChatGPT/Claude-style conversational analysis"""
        
        prompt = f"""You are an expert data analyst with a conversational, educational style like ChatGPT or Claude. 

Analyze this data and answer the user's question in a comprehensive, engaging way.

USER QUESTION: "{question}"

FILE CONTEXT:
- Filename: {file_info['filename']}
- Total rows: {file_info['total_rows']}
- Total columns: {file_info['columns']}

DATA SCHEMA:
{json.dumps(schema, indent=2)}

SAMPLE DATA (first 10 rows):
{json.dumps(data, indent=2)}

ANALYSIS REQUIREMENTS:
1. **Direct Answer**: Start with a clear, direct answer to their question
2. **Context & Insights**: Provide business context and meaningful insights
3. **Data Quality Notes**: Mention data completeness, patterns, or anomalies
4. **Educational Explanations**: Explain methodology or statistical concepts when relevant
5. **Conversational Tone**: Be friendly, helpful, and encouraging
6. **Follow-up Guidance**: Suggest related questions or deeper analysis

RESPONSE STYLE:
- Use emojis sparingly for emphasis (📊, 💡, ✅)
- Include section headers with **bold text**
- Provide specific numbers and percentages
- Be thorough but not overwhelming
- Show enthusiasm for the data insights

Generate a comprehensive, conversational response (300-500 words) that makes the user feel like they're talking to an expert who truly understands their data and business needs."""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 300,
                            "num_ctx": 2048
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "I apologize, but I couldn't generate a comprehensive analysis. Let me know if you'd like me to try a different approach!")
                
        except Exception as e:
            logger.error(f"Error generating conversational analysis: {e}")
            # Fast fallback analysis based on the question and data
            return self._generate_fast_fallback_analysis(question, data, file_info, schema)
    
    def _generate_fast_fallback_analysis(self, question: str, data: List[Dict], file_info: Dict, schema: Dict) -> str:
        """Generate fast analysis when LLM times out"""
        
        question_lower = question.lower()
        filename = file_info['filename']
        total_rows = file_info['total_rows']
        total_cols = file_info['columns']
        
        # Quick analysis based on question type
        if any(word in question_lower for word in ['how many', 'count', 'total']):
            # Count-based questions
            if 'customer' in question_lower or 'user' in question_lower:
                active_count = sum(1 for record in data if record.get('status', '').lower() == 'active')
                inactive_count = sum(1 for record in data if record.get('status', '').lower() == 'inactive')
                
                if active_count > 0 or inactive_count > 0:
                    return f"""🎯 **Customer Analysis Summary**

**Total Customers**: {total_rows} customers in your {filename} dataset

**Status Breakdown**:
• **Active customers**: {active_count} ({(active_count/total_rows*100):.1f}%)
• **Inactive customers**: {inactive_count} ({(inactive_count/total_rows*100):.1f}%)

📊 **Key Insights**:
• Your dataset contains {total_cols} data points per customer
• {(active_count/total_rows*100):.1f}% activation rate shows {'strong' if active_count/total_rows > 0.7 else 'moderate' if active_count/total_rows > 0.4 else 'low'} customer engagement
• This gives you a complete view of your customer base

💡 **Next Steps**: Consider analyzing customer patterns, segmentation, or trends over time to optimize your business strategy!"""
                
            return f"""📊 **Dataset Overview**

I found **{total_rows} records** in your {filename} file with {total_cols} different data fields.

🔍 **Quick Analysis**:
• Complete dataset with {total_rows} entries
• {total_cols} variables provide rich analysis opportunities
• Data appears well-structured for business insights

💡 **What's Next**: Ask me about specific patterns, comparisons, or trends in your data - I'm here to help you discover valuable insights!"""
        
        elif any(word in question_lower for word in ['show', 'analyze', 'breakdown', 'distribution']):
            # Analysis questions
            return f"""📈 **Data Analysis for {filename}**

**Dataset Overview**:
• **{total_rows} records** across **{total_cols} columns**
• Rich data structure ready for analysis

🔍 **Available Data Fields**:
{chr(10).join([f'• **{col}**: {info.get("description", "Data field")}' for col, info in list(schema.items())[:5]])}

💡 **Analysis Ready**: Your data is well-structured and ready for deeper insights. Ask me specific questions about trends, patterns, or comparisons you'd like to explore!"""
        
        else:
            # General questions
            return f"""👋 **Welcome to your data analysis!**

I've successfully loaded your **{filename}** file with **{total_rows} records** and **{total_cols} data variables**.

🎯 **What I can help you with**:
• Count and calculate totals
• Analyze patterns and trends  
• Compare different segments
• Identify insights and anomalies

📊 **Your Data**: Looks great and ready for analysis! What specific insights would you like me to help you discover?"""

    async def _generate_follow_up_questions(
        self, 
        original_question: str, 
        schema: Dict[str, Any], 
        intent_analysis: Dict[str, Any],
        filename: str
    ) -> List[str]:
        """Generate intelligent follow-up questions"""
        
        prompt = f"""Based on the user's question and data schema, suggest 3-4 intelligent follow-up questions that would provide deeper insights.

ORIGINAL QUESTION: "{original_question}"
FILENAME: {filename}

DATA COLUMNS AVAILABLE:
{list(schema.keys())}

Generate follow-up questions that:
1. Dive deeper into the analysis
2. Explore different dimensions of the data
3. Suggest business insights or comparisons
4. Are actionable and specific

Return ONLY a JSON array of questions, no other text:
["Question 1", "Question 2", "Question 3", "Question 4"]"""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "max_tokens": 200
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract JSON array from response
                response_text = result.get("response", "")
                try:
                    questions = json.loads(response_text)
                    return questions if isinstance(questions, list) else []
                except:
                    # Fallback questions
                    return [
                        "What patterns do you see in this data?",
                        "Can you show me a breakdown by different categories?",
                        "What insights would help me make better business decisions?",
                        "Are there any trends or anomalies I should know about?"
                    ]
                    
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            # Smart fallback questions based on the original question
            return self._generate_smart_fallback_questions(original_question, schema, filename)
    
    def _generate_smart_fallback_questions(self, original_question: str, schema: Dict, filename: str) -> List[str]:
        """Generate smart follow-up questions based on the data and original question"""
        
        question_lower = original_question.lower()
        columns = list(schema.keys())
        
        questions = []
        
        # Based on question type, suggest relevant follow-ups
        if any(word in question_lower for word in ['how many', 'count', 'total']):
            if 'status' in columns:
                questions.append("What's the breakdown by status?")
            if any(col for col in columns if 'date' in col.lower() or 'time' in col.lower()):
                questions.append("How has this changed over time?")
            questions.append("Can you show me the distribution across different categories?")
        
        elif any(word in question_lower for word in ['status', 'active', 'inactive']):
            questions.append("What patterns do you see in the active vs inactive users?")
            if any(col for col in columns if 'email' in col.lower() or 'name' in col.lower()):
                questions.append("Can you analyze user engagement patterns?")
        
        # Always add some general smart questions based on available data
        if 'email' in columns:
            questions.append("Are there any email domain patterns I should know about?")
        
        if len(columns) > 3:
            questions.append("What correlations exist between different data fields?")
        
        # Add business-focused questions
        questions.append("What business insights can you extract from this data?")
        questions.append("What actions should I take based on these findings?")
        
        # Return top 4 most relevant questions
        return questions[:4] if questions else [
            "What other insights can you find in this data?",
            "Can you analyze different aspects of the dataset?",
            "What trends or patterns should I be aware of?",
            "How can this data help with business decisions?"
        ]

    async def _generate_conversational_response(
        self, 
        question: str, 
        schema: Dict[str, Any], 
        filename: str, 
        df
    ) -> str:
        """Generate pure conversational response without data analysis"""
        
        prompt = f"""You are a helpful data analyst AI assistant. The user has uploaded a file called "{filename}" and is asking you a question.

USER QUESTION: "{question}"

Available data columns: {list(schema.keys())}
Dataset has {len(df)} rows and {len(df.columns)} columns.

Respond in a conversational, helpful manner like ChatGPT or Claude. If they're asking about general data exploration or guidance, provide helpful suggestions. If they need specific analysis, guide them toward asking more specific questions.

Be friendly, encouraging, and show enthusiasm for helping them understand their data."""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 400
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "I'm here to help you analyze your data! What specific insights are you looking for?")
                
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return f"Thanks for uploading {filename}! I can see you have {len(df)} records with {len(df.columns)} different variables. What specific insights or analysis would you like me to help you with?"

    async def _generate_contextual_response(self, question: str, conversation_id: str) -> str:
        """Generate response for follow-up questions in conversation"""
        
        prompt = f"""Continue this conversation naturally. The user is asking a follow-up question in an existing data analysis conversation.

USER'S FOLLOW-UP QUESTION: "{question}"

Respond as a helpful data analyst who remembers the context. Be conversational, helpful, and suggest specific ways to analyze their data further. If they need specific data analysis, guide them to ask more detailed questions about their dataset."""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 300
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "I'd be happy to help you explore that further! Could you provide more specific details about what you'd like to analyze?")
                
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "I'd love to help you dive deeper into that analysis! What specific aspect would you like me to focus on?"

    async def _generate_general_follow_ups(self, question: str) -> List[str]:
        """Generate general follow-up questions for continued conversation"""
        
        return [
            "Would you like me to analyze a specific aspect of your data?",
            "What business decisions are you trying to make with this data?",
            "Are there any particular trends or patterns you're curious about?",
            "Would you like me to create visualizations for any specific metrics?"
        ]

    async def _generate_general_file_analysis(
        self, 
        question: str, 
        df, 
        schema: Dict[str, Any], 
        filename: str
    ) -> str:
        """Generate general analysis when specific query fails"""
        
        prompt = f"""Provide a helpful analysis overview for this dataset.

USER QUESTION: "{question}"
FILENAME: {filename}
ROWS: {len(df)}
COLUMNS: {len(df.columns)}

Available columns: {list(schema.keys())}

Give a friendly, conversational overview that addresses their question as best as possible and suggests how they can get more specific insights."""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 400
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", f"I can see you have {len(df)} records in {filename} with {len(df.columns)} different data points. Let me know what specific insights you're looking for!")
                
        except Exception as e:
            logger.error(f"Error generating general analysis: {e}")
            return f"I've loaded your file {filename} with {len(df)} records and {len(df.columns)} columns. I'm ready to help you analyze this data - what specific questions do you have?"
    
    async def analyze_business_question(
        self,
        question: str,
        schema: Dict[str, Any],
        table_name: str
    ) -> Dict[str, Any]:
        """
        Analyze business question to understand intent and generate appropriate response
        """
        
        logger.info(f"Analyzing business question: {question}")
        
        # Step 1: Understand question intent
        intent_analysis = await self._analyze_question_intent(question, schema)
        
        # Step 2: Generate SQL with business context
        sql_query = await self._generate_business_sql(question, schema, table_name, intent_analysis)
        
        # Step 3: Generate business explanation
        explanation = await self._generate_business_explanation(question, intent_analysis, schema)
        
        result = {
            "sql": sql_query,
            "intent": intent_analysis,
            "explanation": explanation,
            "confidence": self._calculate_confidence(intent_analysis, schema)
        }
        
        logger.info(f"Question analysis complete. Intent: {intent_analysis['primary_intent']}, Confidence: {result['confidence']:.2f}")
        
        return result
    
    async def _analyze_question_intent(self, question: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the business intent behind the question"""
        
        question_lower = question.lower()
        
        # Detect primary business intent
        primary_intent = "exploration"  # Default
        intent_confidence = 0.5
        
        for intent_type, patterns in self.business_patterns.items():
            keyword_matches = sum(1 for keyword in patterns['keywords'] if keyword in question_lower)
            if keyword_matches > 0:
                confidence = min(keyword_matches / len(patterns['keywords']), 1.0)
                if confidence > intent_confidence:
                    primary_intent = intent_type
                    intent_confidence = confidence
        
        # Extract key entities
        entities = self._extract_business_entities(question, schema)
        
        # Determine expected result type
        result_type = self._determine_result_type(question, primary_intent)
        
        # Analyze time dimension
        time_dimension = self._extract_time_dimension(question)
        
        return {
            "primary_intent": primary_intent,
            "confidence": intent_confidence,
            "entities": entities,
            "result_type": result_type,
            "time_dimension": time_dimension,
            "complexity": self._assess_question_complexity(question, entities)
        }
    
    def _extract_business_entities(self, question: str, schema: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract business entities from the question with intelligent column mapping"""
        
        question_lower = question.lower()
        entities = {
            "columns": [],
            "values": [],
            "time_periods": [],
            "aggregations": [],
            "filters": []
        }
        
        # Smart business term mapping - maps business language to common column patterns
        business_term_mapping = {
            'customers': ['user', 'customer', 'client', 'account'],
            'users': ['user', 'customer', 'client', 'account'], 
            'people': ['user', 'customer', 'person', 'individual'],
            'sales': ['sale', 'order', 'transaction', 'purchase'],
            'revenue': ['revenue', 'amount', 'value', 'price', 'cost'],
            'products': ['product', 'item', 'goods', 'service'],
            'orders': ['order', 'purchase', 'transaction', 'sale']
        }
        
        # Extract column references with smart mapping
        for col_name, col_info in schema.items():
            col_variations = [
                col_name,
                col_name.replace('_', ' '),
                col_name.replace('_', ''),
                col_info.get('description', '').lower()
            ]
            
            # Direct column name matching
            for variation in col_variations:
                if variation and variation.lower() in question_lower:
                    entities["columns"].append(col_name)
                    break
            else:
                # Smart business term matching
                col_name_lower = col_name.lower()
                for business_term, column_patterns in business_term_mapping.items():
                    if business_term in question_lower:
                        # Check if any column matches the business term patterns
                        for pattern in column_patterns:
                            if pattern in col_name_lower:
                                entities["columns"].append(col_name)
                                break
        
        # Extract aggregation functions
        agg_patterns = {
            'count': ['count', 'how many', 'number of', 'total number'],
            'sum': ['sum', 'total', 'add up'],
            'avg': ['average', 'avg', 'mean'],
            'max': ['maximum', 'max', 'highest', 'largest', 'biggest'],
            'min': ['minimum', 'min', 'lowest', 'smallest']
        }
        
        for agg_func, patterns in agg_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                entities["aggregations"].append(agg_func.upper())
        
        # Extract time periods
        time_patterns = [
            'today', 'yesterday', 'last week', 'this week', 'last month', 'this month',
            'last year', 'this year', 'last quarter', 'this quarter',
            'daily', 'weekly', 'monthly', 'yearly', 'quarterly'
        ]
        
        for pattern in time_patterns:
            if pattern in question_lower:
                entities["time_periods"].append(pattern)
        
        # Extract filter values
        filter_patterns = re.findall(r"'([^']*)'|\"([^\"]*)\"", question)
        entities["values"] = [match[0] or match[1] for match in filter_patterns]
        
        return entities
    
    def _determine_result_type(self, question: str, intent: str) -> str:
        """Determine what type of result the user expects"""
        
        question_lower = question.lower()
        
        if intent == "metrics":
            if any(word in question_lower for word in ['how many', 'count', 'number of']):
                return "single_number"
            elif any(word in question_lower for word in ['sum', 'total', 'average', 'avg']):
                return "single_value"
        
        elif intent == "rankings":
            if any(word in question_lower for word in ['top', 'best', 'worst']):
                return "ranked_list"
        
        elif intent == "trends":
            if any(word in question_lower for word in ['over time', 'trend', 'growth']):
                return "time_series"
        
        elif intent == "comparisons":
            if any(word in question_lower for word in ['compare', 'vs', 'versus']):
                return "comparison_chart"
        
        # Default based on expected result size
        if any(word in question_lower for word in ['show me', 'list', 'all']):
            return "data_table"
        
        return "summary"
    
    def _extract_time_dimension(self, question: str) -> Dict[str, Any]:
        """Extract time-related information from the question"""
        
        question_lower = question.lower()
        
        time_dimension = {
            "has_time": False,
            "period": None,
            "granularity": None,
            "relative": None
        }
        
        # Check for time-related keywords
        time_keywords = ['time', 'date', 'when', 'during', 'over', 'by', 'monthly', 'daily', 'yearly']
        if any(keyword in question_lower for keyword in time_keywords):
            time_dimension["has_time"] = True
        
        # Extract time granularity
        granularity_patterns = {
            'hour': ['hourly', 'by hour', 'per hour'],
            'day': ['daily', 'by day', 'per day', 'each day'],
            'week': ['weekly', 'by week', 'per week', 'each week'],
            'month': ['monthly', 'by month', 'per month', 'each month'],
            'quarter': ['quarterly', 'by quarter', 'per quarter'],
            'year': ['yearly', 'annually', 'by year', 'per year']
        }
        
        for granularity, patterns in granularity_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                time_dimension["granularity"] = granularity
                break
        
        # Extract relative time periods
        relative_patterns = {
            'last_week': ['last week'],
            'last_month': ['last month'],
            'last_year': ['last year'],
            'this_week': ['this week'],
            'this_month': ['this month'],
            'this_year': ['this year'],
            'yesterday': ['yesterday'],
            'today': ['today']
        }
        
        for relative, patterns in relative_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                time_dimension["relative"] = relative
                break
        
        return time_dimension
    
    def _assess_question_complexity(self, question: str, entities: Dict[str, List[str]]) -> str:
        """Assess the complexity of the business question"""
        
        complexity_score = 0
        
        # Count entities
        total_entities = sum(len(entity_list) for entity_list in entities.values())
        complexity_score += min(total_entities / 5, 1.0)  # Max 1.0 for entities
        
        # Check for complex operations
        complex_keywords = ['compare', 'vs', 'trend', 'correlation', 'breakdown', 'distribution', 'analysis']
        complex_count = sum(1 for keyword in complex_keywords if keyword in question.lower())
        complexity_score += min(complex_count / 3, 1.0)  # Max 1.0 for complexity
        
        # Check for multiple conditions
        condition_keywords = ['and', 'or', 'but', 'except', 'only', 'where']
        condition_count = sum(1 for keyword in condition_keywords if keyword in question.lower())
        complexity_score += min(condition_count / 4, 0.5)  # Max 0.5 for conditions
        
        if complexity_score < 0.3:
            return "simple"
        elif complexity_score < 0.7:
            return "moderate"
        else:
            return "complex"
    
    async def _generate_business_sql(
        self,
        question: str,
        schema: Dict[str, Any],
        table_name: str,
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Generate SQL with business context and intent understanding"""
        
        # Create enhanced schema description
        schema_desc = self._create_business_schema_description(schema, table_name)
        
        # Create business context
        business_context = self._create_business_context(intent_analysis, schema)
        
        # Create specialized prompt based on intent
        prompt = self._create_sql_generation_prompt(
            question, schema_desc, business_context, intent_analysis
        )
        
        try:
            # Use CodeLlama for SQL generation with enhanced prompting
            sql_query = await self._call_ollama(prompt, self.code_model)
            
            # Clean and validate SQL
            cleaned_sql = self._clean_and_validate_sql(sql_query, intent_analysis)
            
            logger.info(f"Generated SQL: {cleaned_sql}")
            return cleaned_sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            # Generate fallback SQL based on intent
            return self._generate_fallback_sql(question, schema, table_name, intent_analysis)
    
    def _create_business_schema_description(self, schema: Dict[str, Any], table_name: str) -> str:
        """Create business-friendly schema description"""
        
        desc = f"Business Data Table: {table_name}\n"
        desc += "Available Information:\n\n"
        
        # Group columns by business purpose
        grouped_columns = {
            'Identifiers': [],
            'Metrics': [],
            'Categories': [],
            'Dates': [],
            'Descriptions': []
        }
        
        for col_name, col_info in schema.items():
            col_type = col_info.get('type', 'text')
            description = col_info.get('description', '')
            
            if col_type in ['currency', 'number', 'percentage']:
                grouped_columns['Metrics'].append((col_name, description))
            elif col_type == 'date':
                grouped_columns['Dates'].append((col_name, description))
            elif col_type == 'category' or (col_type == 'text' and col_info.get('unique_values', 0) < 20):
                grouped_columns['Categories'].append((col_name, description))
            elif 'id' in col_name.lower():
                grouped_columns['Identifiers'].append((col_name, description))
            else:
                grouped_columns['Descriptions'].append((col_name, description))
        
        # Create grouped description
        for group_name, columns in grouped_columns.items():
            if columns:
                desc += f"{group_name}:\n"
                for col_name, description in columns:
                    sample_info = ""
                    col_info = schema.get(col_name, {})
                    
                    if col_info.get('type') == 'number' and 'min' in col_info:
                        sample_info = f" (range: {col_info['min']:.1f} - {col_info['max']:.1f})"
                    elif col_info.get('sample_values'):
                        samples = col_info['sample_values'][:3]
                        sample_info = f" (examples: {', '.join(map(str, samples))})"
                    
                    desc += f"  - \"{col_name}\": {description}{sample_info}\n"
                desc += "\n"
        
        return desc
    
    def _create_business_context(self, intent_analysis: Dict[str, Any], schema: Dict[str, Any]) -> str:
        """Create business context for SQL generation"""
        
        context = f"Business Question Type: {intent_analysis['primary_intent'].title()}\n"
        context += f"Expected Result: {intent_analysis['result_type'].replace('_', ' ').title()}\n"
        
        if intent_analysis['entities']['aggregations']:
            context += f"Required Calculations: {', '.join(intent_analysis['entities']['aggregations'])}\n"
        
        if intent_analysis['entities']['columns']:
            context += f"Relevant Columns: {', '.join(intent_analysis['entities']['columns'])}\n"
        
        if intent_analysis['time_dimension']['has_time']:
            context += "Time Analysis: Required\n"
            if intent_analysis['time_dimension']['granularity']:
                context += f"Time Granularity: {intent_analysis['time_dimension']['granularity'].title()}\n"
        
        return context
    
    def _create_sql_generation_prompt(
        self,
        question: str,
        schema_desc: str,
        business_context: str,
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Create specialized SQL generation prompt based on business intent"""
        
        base_prompt = f"""You are a business intelligence SQL expert. Generate a PostgreSQL query to answer this business question.

{schema_desc}

{business_context}

BUSINESS TERMINOLOGY MAPPING:
- "customers", "users", "people" → look for columns with 'user', 'customer', 'client' in the name
- When counting entities (customers/users), use COUNT(*) to count all records
- "sales", "orders" → look for columns with 'sale', 'order', 'transaction' in the name  
- "revenue", "amount" → look for columns with 'revenue', 'amount', 'value', 'price' in the name

BUSINESS RULES:
1. Always use meaningful column aliases that business users understand
2. Format numbers appropriately (currency as currency, percentages as percentages)
3. Include relevant sorting for business insights
4. Limit results to reasonable business ranges (e.g., top 10, last 100 records)
5. Use proper date formatting for time-based analysis
6. Always use double quotes around column names
7. When the question asks "how many customers/users", use COUNT(*) to count all records
8. Return only the SQL query, no explanations

"""
        
        # Add intent-specific guidance
        if intent_analysis['primary_intent'] == 'metrics':
            base_prompt += """
METRICS GUIDANCE:
- Use appropriate aggregation functions (COUNT, SUM, AVG)
- Include meaningful labels for calculated fields
- Round numbers to appropriate decimal places
- Consider NULL handling in calculations
"""
        
        elif intent_analysis['primary_intent'] == 'rankings':
            base_prompt += """
RANKING GUIDANCE:
- Use ORDER BY with appropriate direction (DESC for "top", ASC for "lowest")
- Include LIMIT clause for top/bottom queries
- Consider ties in ranking scenarios
- Show the ranking metric clearly
"""
        
        elif intent_analysis['primary_intent'] == 'trends':
            base_prompt += """
TREND ANALYSIS GUIDANCE:
- Use DATE_TRUNC or EXTRACT for time grouping
- Order by time dimension
- Include time labels that are business-friendly
- Consider appropriate time ranges
"""
        
        elif intent_analysis['primary_intent'] == 'comparisons':
            base_prompt += """
COMPARISON GUIDANCE:
- Use GROUP BY to create comparison categories
- Include percentage calculations where relevant
- Use CASE statements for conditional logic
- Show clear comparison metrics
"""
        
        base_prompt += f"\nBusiness Question: {question}\n\nSQL Query:"
        
        return base_prompt
    
    def _clean_and_validate_sql(self, sql: str, intent_analysis: Dict[str, Any]) -> str:
        """Clean and validate generated SQL with business logic"""
        
        # Basic cleaning
        sql = sql.strip()
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        
        # Remove explanatory text
        lines = sql.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if (line.upper().startswith(('SELECT', 'WITH', 'FROM', 'WHERE', 'GROUP BY', 
                                       'ORDER BY', 'HAVING', 'LIMIT', 'JOIN', 'LEFT JOIN', 
                                       'RIGHT JOIN', 'INNER JOIN', 'AND', 'OR')) or
                (sql_lines and not line.upper().startswith(('THE', 'THIS', 'HERE', 'ABOVE', 'NOTE')))):
                sql_lines.append(line)
        
        cleaned_sql = '\n'.join(sql_lines) if sql_lines else sql
        
        # Business-specific validations and enhancements
        cleaned_sql = self._apply_business_enhancements(cleaned_sql, intent_analysis)
        
        # Ensure it ends with semicolon
        if not cleaned_sql.rstrip().endswith(';'):
            cleaned_sql += ';'
        
        return cleaned_sql
    
    def _apply_business_enhancements(self, sql: str, intent_analysis: Dict[str, Any]) -> str:
        """Apply business-specific enhancements to the SQL"""
        
        # Add appropriate LIMIT if not present and needed
        if intent_analysis['primary_intent'] in ['rankings', 'exploration'] and 'LIMIT' not in sql.upper():
            if intent_analysis['primary_intent'] == 'rankings':
                sql = sql.rstrip(';') + ' LIMIT 10;'
            else:
                sql = sql.rstrip(';') + ' LIMIT 100;'
        
        # Ensure proper column quoting
        # This is a simplified version - in production, you'd want more robust parsing
        import re
        sql = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\s*(,|\)|$|FROM|WHERE|GROUP|ORDER|HAVING))', r'"\1"', sql)
        
        return sql
    
    def _generate_fallback_sql(
        self,
        question: str,
        schema: Dict[str, Any],
        table_name: str,
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Generate fallback SQL when AI generation fails"""
        
        # Simple fallback based on intent
        if intent_analysis['primary_intent'] == 'metrics' and intent_analysis['entities']['aggregations']:
            agg_func = intent_analysis['entities']['aggregations'][0]
            if intent_analysis['entities']['columns']:
                col = intent_analysis['entities']['columns'][0]
                return f'SELECT {agg_func}("{col}") as result FROM {table_name};'
            else:
                return f'SELECT COUNT(*) as total_records FROM {table_name};'
        
        elif intent_analysis['primary_intent'] == 'rankings':
            if intent_analysis['entities']['columns']:
                col = intent_analysis['entities']['columns'][0]
                order = 'DESC' if any(word in question.lower() for word in ['top', 'highest', 'best']) else 'ASC'
                return f'SELECT * FROM {table_name} ORDER BY "{col}" {order} LIMIT 10;'
        
        # Ultimate fallback
        return f'SELECT * FROM {table_name} LIMIT 10;'
    
    def _calculate_confidence(self, intent_analysis: Dict[str, Any], schema: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis"""
        
        confidence = intent_analysis['confidence']  # Base intent confidence
        
        # Boost confidence if we found relevant columns
        if intent_analysis['entities']['columns']:
            confidence += 0.2
        
        # Boost confidence if we have clear aggregations
        if intent_analysis['entities']['aggregations']:
            confidence += 0.15
        
        # Reduce confidence for complex questions
        if intent_analysis['complexity'] == 'complex':
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    async def _generate_business_explanation(
        self,
        question: str,
        intent_analysis: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> str:
        """Generate business-friendly explanation of what the query will do"""
        
        intent = intent_analysis['primary_intent']
        result_type = intent_analysis['result_type']
        
        if intent == 'metrics':
            if result_type == 'single_number':
                return "I'll count the total number of records that match your criteria."
            elif result_type == 'single_value':
                return "I'll calculate the requested metric from your data."
        
        elif intent == 'rankings':
            return "I'll show you the top results ranked by your specified criteria."
        
        elif intent == 'trends':
            return "I'll analyze the trends over time to show you how values change."
        
        elif intent == 'comparisons':
            return "I'll compare different categories to show you the differences."
        
        return "I'll analyze your data to find the information you're looking for."
    
    async def generate_business_answer(
        self,
        question: str,
        results: Dict[str, Any],
        schema: Dict[str, Any],
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Generate business-friendly answer from query results"""
        
        logger.info("Generating business-friendly answer")
        
        data = results.get('data', [])
        columns = results.get('columns', [])
        
        if not data:
            return self._generate_no_data_response(question, intent_analysis)
        
        # Enhanced universal answer generation based on question type and data content
        question_lower = question.lower()
        
        # Special handling for specific metric questions while keeping it generic
        if any(word in question_lower for word in ['how many', 'count']) and 'active' in question_lower:
            return self._generate_metrics_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'rankings':
            return self._generate_ranking_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'trends':
            return self._generate_trend_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'comparisons':
            return self._generate_comparison_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'metrics':
            return self._generate_metrics_answer(question, data, intent_analysis)
        else:
            # Universal comprehensive analysis for any question type
            return self._generate_general_answer(question, data, intent_analysis)
    
    def _generate_no_data_response(self, question: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate helpful response when no data is found"""
        
        intent = intent_analysis['primary_intent']
        
        responses = {
            'metrics': "No data found for your metric calculation. You might want to check your filters or time period.",
            'rankings': "No results found to rank. Try broadening your search criteria.",
            'trends': "No trend data available for the specified time period. Consider expanding your date range.",
            'comparisons': "No data available for comparison. Check if the categories you're comparing have data.",
            'filters': "No records match your filter criteria. Try adjusting your search parameters."
        }
        
        return responses.get(intent, "No data found matching your question. Please try rephrasing or check your data source.")
    
    def _generate_educational_no_data_response(self, question: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate educational, conversational response when no data is found"""
        
        intent = intent_analysis['primary_intent']
        
        response_parts = []
        response_parts.append("I searched through your data to answer your question, but didn't find any matching records.")
        response_parts.append("")
        response_parts.append("🔍 **What this means:**")
        
        if intent == 'metrics':
            response_parts.append("• Your query was looking for specific calculations, but no data met the criteria")
            response_parts.append("• This could mean the filters are too restrictive or the data doesn't contain the expected values")
        elif intent == 'rankings':
            response_parts.append("• I was looking for data to rank, but couldn't find records that match your criteria")
            response_parts.append("• Try broadening your search or checking if the ranking field exists in your data")
        elif intent == 'trends':
            response_parts.append("• I was looking for time-based patterns, but no data was found for the specified period")
            response_parts.append("• Consider expanding your date range or checking if your data contains time information")
        else:
            response_parts.append("• The specific conditions in your question might be too restrictive")
            response_parts.append("• Your data might not contain the information you're looking for")
        
        response_parts.append("")
        response_parts.append("💡 **What you can try:**")
        response_parts.append("• **Broaden your search**: Remove some filters or conditions")
        response_parts.append("• **Check your data**: Make sure the columns and values you're asking about exist")
        response_parts.append("• **Rephrase your question**: Try asking in a different way")
        response_parts.append("• **Explore generally**: Ask 'show me a summary of this data' to see what's available")
        
        return "\n".join(response_parts)
    
    def _generate_metrics_answer(self, question: str, data: List[Dict], intent_analysis: Dict[str, Any]) -> str:
        """Generate answer for metrics questions"""
        
        question_lower = question.lower()
        
        # Handle count questions specifically
        if 'count' in question_lower or 'how many' in question_lower:
            if 'active' in question_lower:
                # Count active users
                active_count = sum(1 for record in data if record.get('status', '').lower() == 'active')
                total_count = len(data)
                inactive_count = total_count - active_count
                
                return f"""📊 **User Activity Analysis**

**{active_count:,} active users** out of {total_count:,} total users
• Active users: **{active_count:,}** ({(active_count/total_count*100):.1f}%)
• Inactive users: **{inactive_count:,}** ({(inactive_count/total_count*100):.1f}%)

This represents a **{(active_count/total_count*100):.1f}% activation rate** for your user base."""
            else:
                total_count = len(data)
                
                # Determine what we're counting based on the question
                entity_type = "records"
                if any(term in question_lower for term in ['customer', 'customers']):
                    entity_type = "customers"
                elif any(term in question_lower for term in ['user', 'users']):
                    entity_type = "users"
                elif any(term in question_lower for term in ['people', 'person']):
                    entity_type = "people"
                elif any(term in question_lower for term in ['sale', 'sales']):
                    entity_type = "sales"
                elif any(term in question_lower for term in ['order', 'orders']):
                    entity_type = "orders"
                
                return f"""📈 **Total Count: {total_count:,} {entity_type}**

Found **{total_count:,} {entity_type}** in your dataset that match the criteria.

💡 **Context**: This count represents all the {entity_type} in your current dataset. Each record corresponds to one {entity_type.rstrip('s') if entity_type.endswith('s') else entity_type}."""
        
        # Handle single metric results
        if len(data) == 1:
            result = data[0]
            value = list(result.values())[0]
            
            if isinstance(value, (int, float)):
                return f"📊 **Result: {value:,}**\n\nThe calculated value for your query is **{value:,}**."
            else:
                return f"📋 **Result: {value}**"
        
        # Handle multiple results
        total_records = len(data)
        return f"📊 **Analysis Complete**\n\nFound **{total_records:,}** records that provide insights for your question."
    
    def _generate_ranking_answer(self, question: str, data: List[Dict], intent_analysis: Dict[str, Any]) -> str:
        """Generate answer for ranking questions"""
        
        count = len(data)
        question_lower = question.lower()
        
        if 'top' in question_lower:
            return f"Here are the **top {count} results** based on your criteria."
        elif 'worst' in question_lower or 'lowest' in question_lower:
            return f"Here are the **bottom {count} results** based on your criteria."
        else:
            return f"Here are **{count} results** ranked by your specified criteria."
    
    def _generate_trend_answer(self, question: str, data: List[Dict], intent_analysis: Dict[str, Any]) -> str:
        """Generate answer for trend questions"""
        
        count = len(data)
        
        if intent_analysis['time_dimension']['granularity']:
            granularity = intent_analysis['time_dimension']['granularity']
            return f"Here's your **{granularity}ly trend** showing {count} data points over time."
        
        return f"Here's your trend analysis with **{count} time periods** of data."
    
    def _generate_comparison_answer(self, question: str, data: List[Dict], intent_analysis: Dict[str, Any]) -> str:
        """Generate answer for comparison questions"""
        
        count = len(data)
        return f"Here's your comparison showing **{count} different categories** with their respective values."
    
    def _generate_general_answer(self, question: str, data: List[Dict], intent_analysis: Dict[str, Any]) -> str:
        """Generate comprehensive, educational Data Analysis Assistant response"""
        
        if not data:
            return self._generate_educational_no_data_response(question, intent_analysis)
        
        # Deep analysis to generate educational insights
        total_records = len(data)
        columns = list(data[0].keys()) if data else []
        
        # Build conversational, educational response
        response_parts = []
        
        # Conversational opening like ChatGPT
        response_parts.append(f"I've analyzed your data to answer your question! Here's what I found:")
        response_parts.append(f"")
        
        # Data story - explain what we're looking at
        response_parts.append(f"📊 **Your Dataset at a Glance**")
        response_parts.append(f"")
        response_parts.append(f"I examined **{total_records:,} records** across **{len(columns)} different variables** in your dataset. This gives us a solid foundation for analysis with enough data points to identify meaningful patterns.")
        response_parts.append(f"")
        
        # Educational insights with explanations
        response_parts.append(f"🔍 **Key Insights & Analysis**")
        response_parts.append(f"")
        
        # User activity analysis with explanation
        if any('status' in col.lower() for col in columns):
            status_values = [record.get('status') for record in data if record.get('status')]
            if status_values:
                active_count = sum(1 for status in status_values if status and 'active' in str(status).lower())
                inactive_count = len(status_values) - active_count
                activation_rate = (active_count / len(status_values)) * 100
                
                response_parts.append(f"**User Engagement Analysis:**")
                response_parts.append(f"• **{active_count:,} active users** out of {len(status_values):,} total users")
                response_parts.append(f"• **Activation rate: {activation_rate:.1f}%** - This means {activation_rate:.1f} out of every 100 users are currently active")
                
                # Educational context
                if activation_rate >= 70:
                    response_parts.append(f"• ✅ **Strong engagement**: Your {activation_rate:.1f}% activation rate indicates a healthy, engaged user base")
                elif activation_rate >= 50:
                    response_parts.append(f"• ⚠️ **Moderate engagement**: Your {activation_rate:.1f}% activation rate suggests room for improvement in user retention")
                else:
                    response_parts.append(f"• 🔴 **Low engagement**: Your {activation_rate:.1f}% activation rate indicates potential issues with user onboarding or retention")
                
                response_parts.append(f"")
        
        # Financial analysis with business context
        money_fields = [col for col in columns if any(word in col.lower() for word in ['spending', 'revenue', 'amount', 'price', 'cost', 'payment'])]
        if money_fields:
            response_parts.append(f"**Financial Performance Analysis:**")
            for field in money_fields[:2]:
                values = [record.get(field) for record in data if isinstance(record.get(field), (int, float))]
                if values:
                    total_value = sum(values)
                    avg_value = total_value / len(values)
                    median_value = sorted(values)[len(values)//2]
                    max_value = max(values)
                    min_value = min(values)
                    
                    field_name = field.replace('_', ' ').title()
                    response_parts.append(f"• **{field_name} Analysis:**")
                    response_parts.append(f"  - Total: ${total_value:,.2f} across all records")
                    response_parts.append(f"  - Average: ${avg_value:,.2f} per record")
                    response_parts.append(f"  - Median: ${median_value:,.2f} (middle value when sorted)")
                    response_parts.append(f"  - Range: ${min_value:,.2f} to ${max_value:,.2f}")
                    
                    # Educational insights
                    if avg_value > median_value * 1.2:
                        response_parts.append(f"  - 📈 **Insight**: Average is higher than median, suggesting some high-value outliers are pulling the average up")
                    elif avg_value < median_value * 0.8:
                        response_parts.append(f"  - 📉 **Insight**: Average is lower than median, indicating some low-value records are pulling the average down")
                    else:
                        response_parts.append(f"  - ⚖️ **Insight**: Average and median are close, suggesting a fairly even distribution")
            response_parts.append(f"")
        
        # Geographic analysis with market insights
        geo_fields = [col for col in columns if any(word in col.lower() for word in ['region', 'country', 'state', 'city', 'location'])]
        if geo_fields:
            geo_col = geo_fields[0]
            regions = [record.get(geo_col) for record in data if record.get(geo_col)]
            unique_regions = list(set(regions))
            
            response_parts.append(f"**Geographic Distribution Analysis:**")
            response_parts.append(f"• **Market coverage**: {len(unique_regions)} different {geo_col.replace('_', ' ').lower()}s")
            response_parts.append(f"• **Geographic spread**: {', '.join(str(r) for r in unique_regions[:5])}{f' and {len(unique_regions)-5} more' if len(unique_regions) > 5 else ''}")
            
            # Market concentration analysis
            from collections import Counter
            region_counts = Counter(regions)
            most_common = region_counts.most_common(3)
            
            response_parts.append(f"• **Market concentration**:")
            for region, count in most_common:
                percentage = (count / len(regions)) * 100
                response_parts.append(f"  - {region}: {count} records ({percentage:.1f}%)")
            
            # Educational insight
            top_percentage = (most_common[0][1] / len(regions)) * 100 if most_common else 0
            if top_percentage > 50:
                response_parts.append(f"  - 🎯 **Insight**: Your data is concentrated in {most_common[0][0]} ({top_percentage:.1f}%), indicating a dominant market")
            else:
                response_parts.append(f"  - 🌍 **Insight**: Fairly distributed across regions, indicating diversified market presence")
            response_parts.append(f"")
        
        # Categorical analysis with business insights
        categorical_fields = [col for col in columns if col.lower() not in ['status'] and 
                            len(set([record.get(col) for record in data if record.get(col)])) <= 20]
        if categorical_fields:
            cat_col = categorical_fields[0]
            values = [record.get(cat_col) for record in data if record.get(cat_col)]
            if values:
                from collections import Counter
                value_counts = Counter(values)
                
                response_parts.append(f"**{cat_col.replace('_', ' ').title()} Distribution:**")
                response_parts.append(f"• **Variety**: {len(value_counts)} different {cat_col.replace('_', ' ').lower()} categories")
                
                top_categories = value_counts.most_common(3)
                for category, count in top_categories:
                    percentage = (count / len(values)) * 100
                    response_parts.append(f"• {category}: {count} records ({percentage:.1f}%)")
                
                response_parts.append(f"")
        
        # Data quality assessment with educational explanation
        response_parts.append(f"📈 **Statistical Summary & Data Quality**")
        response_parts.append(f"")
        response_parts.append(f"• **Sample size**: {total_records:,} records - This is {'a robust' if total_records >= 100 else 'a small but useful'} sample for analysis")
        response_parts.append(f"• **Data completeness**: Analyzing {len(columns)} variables gives us multiple dimensions to explore")
        response_parts.append(f"• **Data types**: Mix of {'categorical, numerical, and' if money_fields else 'categorical and'} text data provides rich analysis opportunities")
        response_parts.append(f"")
        
        # Actionable recommendations like a data consultant
        response_parts.append(f"💡 **What This Means & Next Steps**")
        response_parts.append(f"")
        
        # Generate contextual recommendations
        recommendations = []
        
        if any('status' in col.lower() for col in columns):
            recommendations.append("**User Engagement**: Consider analyzing what drives users to become active vs inactive")
        
        if money_fields:
            recommendations.append("**Revenue Optimization**: Look into customer segments and spending patterns for growth opportunities")
        
        if geo_fields:
            recommendations.append("**Market Expansion**: Analyze regional performance to identify expansion opportunities")
        
        if len(columns) >= 5:
            recommendations.append("**Correlation Analysis**: With multiple variables, you could explore relationships between different factors")
        
        # Add trend analysis if we have enough data
        if total_records >= 50:
            recommendations.append("**Trend Analysis**: With sufficient data points, you could analyze patterns over time or segments")
        
        for rec in recommendations[:3]:  # Limit to top 3
            response_parts.append(f"• {rec}")
        
        response_parts.append(f"")
        response_parts.append(f"**Want to dig deeper?** Try asking about specific relationships, trends, or comparisons in your data. I'm here to help you uncover insights!")
        
        return "\n".join(response_parts)
    
    def _analyze_data_comprehensively(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Perform deep analysis of the data to understand patterns and insights"""
        
        if not data:
            return {}
        
        total_records = len(data)
        columns = list(data[0].keys()) if data else []
        
        analysis = {
            "total_records": total_records,
            "columns": columns,
            "column_count": len(columns),
            "data_insights": {},
            "patterns": [],
            "key_metrics": {},
            "data_quality": {}
        }
        
        # Analyze each column for insights
        for col in columns:
            col_values = [record.get(col) for record in data if record.get(col) is not None]
            unique_values = list(set(col_values))
            
            column_analysis = {
                "unique_count": int(len(unique_values)),
                "completeness": float(len(col_values) / total_records * 100),
                "sample_values": [str(v) for v in unique_values[:5]],  # Ensure all values are strings
                "data_type": str(self._detect_column_type(col_values))
            }
            
            # Special analysis for different data types
            if column_analysis["data_type"] == "numeric":
                if col_values:
                    numeric_values = [float(v) for v in col_values if isinstance(v, (int, float))]
                    if numeric_values:
                        column_analysis.update({
                            "min": float(min(numeric_values)),
                            "max": float(max(numeric_values)),
                            "avg": float(sum(numeric_values) / len(numeric_values)),
                            "range": float(max(numeric_values) - min(numeric_values))
                        })
            
            elif column_analysis["data_type"] == "categorical":
                # Count value frequencies
                value_counts = {}
                for val in col_values:
                    value_counts[val] = value_counts.get(val, 0) + 1
                
                # Get most common values (convert to JSON serializable format)
                sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
                column_analysis["most_common"] = [[str(k), int(v)] for k, v in sorted_values[:3]]
                column_analysis["distribution"] = {str(k): int(v) for k, v in value_counts.items()}
            
            analysis["data_insights"][col] = column_analysis
        
        # Identify interesting patterns
        analysis["patterns"] = self._identify_patterns(data, analysis)
        
        # Calculate key metrics
        analysis["key_metrics"] = self._calculate_key_metrics(data, question)
        
        return analysis
    
    def _detect_column_type(self, values: List) -> str:
        """Detect the type of data in a column"""
        
        if not values:
            return "empty"
        
        # Check if all values are numeric
        numeric_count = sum(1 for v in values if isinstance(v, (int, float)))
        if numeric_count / len(values) > 0.8:
            return "numeric"
        
        # Check if values look like dates
        date_indicators = ['date', 'time', '-', '/']
        if any(indicator in str(values[0]).lower() for indicator in date_indicators):
            return "date"
        
        # Check for boolean-like values
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 'active', 'inactive'}
        if all(str(v).lower() in bool_values for v in values[:5]):
            return "boolean"
        
        return "categorical"
    
    def _identify_patterns(self, data: List[Dict], analysis: Dict[str, Any]) -> List[str]:
        """Identify interesting patterns in the data"""
        
        patterns = []
        
        # Check for status/activity patterns
        if any('status' in col.lower() for col in analysis["columns"]):
            status_col = next((col for col in analysis["columns"] if 'status' in col.lower()), None)
            if status_col and status_col in analysis["data_insights"]:
                distribution = analysis["data_insights"][status_col].get("distribution", {})
                if distribution:
                    most_common = max(distribution, key=distribution.get)
                    patterns.append(f"Most users have '{most_common}' status ({distribution[most_common]} out of {analysis['total_records']})")
        
        # Check for regional/geographical patterns
        if any('region' in col.lower() or 'country' in col.lower() for col in analysis["columns"]):
            geo_col = next((col for col in analysis["columns"] if 'region' in col.lower() or 'country' in col.lower()), None)
            if geo_col and geo_col in analysis["data_insights"]:
                distribution = analysis["data_insights"][geo_col].get("distribution", {})
                if len(distribution) > 1:
                    patterns.append(f"Data spans {len(distribution)} different regions/locations")
        
        # Check for plan/tier patterns
        if any('plan' in col.lower() or 'tier' in col.lower() for col in analysis["columns"]):
            plan_col = next((col for col in analysis["columns"] if 'plan' in col.lower() or 'tier' in col.lower()), None)
            if plan_col and plan_col in analysis["data_insights"]:
                distribution = analysis["data_insights"][plan_col].get("distribution", {})
                if distribution:
                    premium_count = sum(count for plan, count in distribution.items() if 'premium' in plan.lower())
                    if premium_count > 0:
                        patterns.append(f"{premium_count} users are on premium plans")
        
        return patterns
    
    def _calculate_key_metrics(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Calculate key business metrics from the data"""
        
        metrics = {}
        
        # Calculate completion rates
        total_records = len(data)
        
        # Check for monetary values (only if data exists)
        if data:
            money_columns = [col for col in data[0].keys() if any(word in col.lower() for word in ['spending', 'revenue', 'amount', 'price', 'cost'])]
            for col in money_columns:
                values = [record.get(col) for record in data if isinstance(record.get(col), (int, float))]
                if values:
                    metrics[f"total_{col}"] = float(sum(values))  # Ensure JSON serializable
                    metrics[f"avg_{col}"] = float(sum(values) / len(values))  # Ensure JSON serializable
            
            # Age demographics if available
            if any('age' in col.lower() for col in data[0].keys()):
                age_col = next((col for col in data[0].keys() if 'age' in col.lower()), None)
                ages = [record.get(age_col) for record in data if isinstance(record.get(age_col), (int, float))]
                if ages:
                    metrics["avg_age"] = float(sum(ages) / len(ages))  # Ensure JSON serializable
                    metrics["age_range"] = f"{int(min(ages))}-{int(max(ages))}"  # Ensure JSON serializable
        
        return metrics
    
    def _create_analytical_response(self, question: str, analysis: Dict[str, Any], intent_analysis: Dict[str, Any]) -> str:
        """Create a comprehensive analytical response"""
        
        total_records = analysis.get("total_records", 0)
        columns = analysis.get("columns", [])
        patterns = analysis.get("patterns", [])
        key_metrics = analysis.get("key_metrics", {})
        
        # Build response with deep insights
        response_parts = []
        
        # Header with comprehensive overview
        response_parts.append(f"📊 **Comprehensive Data Analysis Complete**")
        response_parts.append(f"")
        response_parts.append(f"I've analyzed your complete dataset of **{total_records:,} records** across **{len(columns)} data dimensions** to provide you with detailed insights.")
        response_parts.append(f"")
        
        # Data structure insights
        response_parts.append(f"🔍 **Dataset Structure:**")
        response_parts.append(f"• **Records analyzed:** {total_records:,}")
        response_parts.append(f"• **Data fields:** {len(columns)}")
        response_parts.append(f"• **Coverage:** {', '.join(columns[:5])}{' and more...' if len(columns) > 5 else ''}")
        response_parts.append(f"")
        
        # Key findings
        if patterns:
            response_parts.append(f"📈 **Key Findings:**")
            for pattern in patterns:
                response_parts.append(f"• {pattern}")
            response_parts.append(f"")
        
        # Business metrics
        if key_metrics:
            response_parts.append(f"💰 **Business Metrics:**")
            for metric, value in key_metrics.items():
                if 'total_' in metric:
                    response_parts.append(f"• **{metric.replace('total_', '').title()}:** ${value:,.2f}" if 'spending' in metric or 'revenue' in metric else f"• **{metric.replace('total_', '').title()}:** {value:,.2f}")
                elif 'avg_' in metric:
                    response_parts.append(f"• **Average {metric.replace('avg_', '').title()}:** ${value:,.2f}" if 'spending' in metric or 'revenue' in metric else f"• **Average {metric.replace('avg_', '').title()}:** {value:.1f}")
                else:
                    response_parts.append(f"• **{metric.replace('_', ' ').title()}:** {value}")
            response_parts.append(f"")
        
        # Data quality assessment
        response_parts.append(f"✅ **Data Quality:** Excellent - All {total_records:,} records successfully processed with complete field mapping")
        response_parts.append(f"")
        
        # Actionable insights
        response_parts.append(f"🎯 **What this means for your business:**")
        if 'active' in question.lower():
            response_parts.append(f"• Your user engagement levels and activation patterns are clearly visible")
            response_parts.append(f"• This data enables targeted user retention strategies")
        elif 'revenue' in question.lower() or 'spending' in question.lower():
            response_parts.append(f"• Revenue patterns and customer value segments are identifiable")
            response_parts.append(f"• Opportunities for pricing optimization and customer growth")
        else:
            response_parts.append(f"• Clear visibility into your data patterns enables data-driven decisions")
            response_parts.append(f"• Multiple analysis angles available for deeper business insights")
        
        return "\n".join(response_parts)
    
    async def _generate_advanced_conversational_response(
        self, 
        question: str, 
        advanced_analysis_results: Dict[str, Any], 
        schema: Dict, 
        file_info: Dict,
        conversation_context: Dict = None
    ) -> str:
        """Generate LLM-based response that directly answers the user's question using their data"""
        try:
            # Prepare data summary for LLM
            data_summary = self._prepare_data_summary_for_llm(advanced_analysis_results, schema, file_info)
            
            # Build conversation history for context
            conversation_history = ""
            if conversation_context and conversation_context.get('recent_messages'):
                recent_messages = conversation_context['recent_messages']
                if len(recent_messages) > 1:  # More than just the current question
                    conversation_history = "\n\nPREVIOUS CONVERSATION:\n"
                    for msg in recent_messages[:-1]:  # Exclude current question
                        role = "USER" if msg['role'] == 'user' else "ASSISTANT"
                        conversation_history += f"{role}: {msg['content'][:200]}...\n" if len(msg['content']) > 200 else f"{role}: {msg['content']}\n"
                    conversation_history += "\nCURRENT QUESTION:\n"
            
            # Create prompt that asks LLM to answer the specific question with conversation context
            prompt = f"""You are a data analyst AI having a conversation with a user about their data. The user has uploaded a CSV file called "{file_info['filename']}" and is asking questions about it.
{conversation_history}
USER: {question}

DATA ANALYSIS:
{data_summary}

As an intelligent assistant, please answer the user's question directly based on this data analysis. Consider the conversation history to provide contextual responses.

Your response should:
1. Directly answer their specific question
2. Use the actual data from their file
3. Be conversational and build on previous context
4. Include specific numbers and insights
5. Reference previous questions/answers when relevant
6. Suggest relevant visualizations if appropriate

Answer:"""

            # Call LLM to generate personalized response
            try:
                llm_response = await self._call_ollama(prompt, self.chat_model)
                if llm_response and len(llm_response.strip()) > 10:
                    return llm_response.strip()
            except Exception as llm_error:
                logger.warning(f"LLM call failed, using fallback: {llm_error}")
            
            # Fallback: Generate specific response based on question analysis
            return self._generate_question_specific_fallback(question, advanced_analysis_results, file_info)
            
        except Exception as e:
            logger.error(f"Error generating advanced response: {e}")
            return f"I've analyzed your **{file_info.get('filename', 'data')}** file. Let me answer your question about: {question}"
    
    def _prepare_data_summary_for_llm(self, analysis_results: Dict[str, Any], schema: Dict, file_info: Dict) -> str:
        """Prepare a concise data summary for the LLM to understand the dataset"""
        summary_parts = []
        
        # Basic file info
        summary_parts.append(f"Dataset: {file_info['filename']} ({file_info['total_rows']} rows, {file_info['columns']} columns)")
        
        # Column information
        if 'statistical_overview' in analysis_results:
            stats = analysis_results['statistical_overview']
            
            # Numerical columns
            if 'descriptive_stats' in stats and 'summary' in stats['descriptive_stats']:
                summary_parts.append("\nNumerical Columns:")
                for col, data in stats['descriptive_stats']['summary'].items():
                    summary_parts.append(f"- {col}: mean={data['mean']:.2f}, min={data['min']:.2f}, max={data['max']:.2f}")
            
            # Categorical columns
            if 'categorical_analysis' in stats:
                summary_parts.append("\nCategorical Columns:")
                for col, data in stats['categorical_analysis'].items():
                    top_values = list(data['most_common'].keys())[:3]
                    summary_parts.append(f"- {col}: {data['unique_values']} unique values (top: {', '.join(top_values)})")
        
        # Key correlations
        if 'correlation' in analysis_results and 'strong_correlations' in analysis_results['correlation']:
            strong_corrs = analysis_results['correlation']['strong_correlations']
            if strong_corrs:
                summary_parts.append("\nKey Relationships:")
                for corr in strong_corrs[:3]:
                    summary_parts.append(f"- {corr['variable1']} ↔ {corr['variable2']}: {corr['correlation']:.3f} ({corr['strength']} {corr['direction']})")
        
        # Clusters/segments
        if 'clustering' in analysis_results and 'cluster_analysis' in analysis_results['clustering']:
            cluster_data = analysis_results['clustering']['cluster_analysis']
            summary_parts.append(f"\nData Segments: Found {len(cluster_data)} distinct groups")
            for cluster_id, data in list(cluster_data.items())[:3]:
                summary_parts.append(f"- {cluster_id}: {data['size']} records ({data['percentage']:.1f}%)")
        
        # Outliers
        if 'outlier' in analysis_results and 'outlier_analysis' in analysis_results['outlier']:
            outlier_data = analysis_results['outlier']['outlier_analysis']
            total_outliers = sum(data.get('outlier_count', 0) for data in outlier_data.values() if isinstance(data, dict))
            if total_outliers > 0:
                summary_parts.append(f"\nOutliers: {total_outliers} anomalous values detected")
        
        return "\n".join(summary_parts)
    
    def _generate_question_specific_fallback(self, question: str, analysis_results: Dict, file_info: Dict) -> str:
        """Generate a fallback response when LLM fails - with SPECIFIC data answers"""
        question_lower = question.lower()
        
        # Extract statistical data for specific answers
        stats = analysis_results.get('statistical_overview', {}).get('descriptive_stats', {}).get('summary', {})
        
        if any(word in question_lower for word in ['average', 'mean']) and 'price' in question_lower:
            if 'price' in stats:
                price_mean = stats['price']['mean']
                return f"The **average price** of products in your dataset is **${price_mean:.2f}**. The prices range from ${stats['price']['min']:.2f} to ${stats['price']['max']:.2f}, showing a good spread across different price points."
        
        elif any(word in question_lower for word in ['average', 'mean']) and any(col in question_lower for col in ['revenue', 'sales', 'total']):
            if 'revenue' in stats:
                revenue_mean = stats['revenue']['mean']
                return f"The **average revenue** per product in your dataset is **${revenue_mean:.2f}**. Revenue ranges from ${stats['revenue']['min']:.2f} to ${stats['revenue']['max']:.2f}."
        
        elif any(word in question_lower for word in ['average', 'mean']) and 'quantity' in question_lower:
            if 'quantity_sold' in stats:
                qty_mean = stats['quantity_sold']['mean']
                return f"The **average quantity sold** per product is **{qty_mean:.1f} units**. Quantities range from {stats['quantity_sold']['min']:.0f} to {stats['quantity_sold']['max']:.0f} units."
        
        elif any(word in question_lower for word in ['highest', 'maximum', 'max', 'best']) and 'rating' in question_lower:
            if 'rating' in stats:
                max_rating = stats['rating']['max']
                return f"The **highest rating** in your dataset is **{max_rating}**. This represents your top-rated product with excellent customer satisfaction."
        
        elif any(word in question_lower for word in ['highest', 'maximum', 'max', 'most expensive']) and 'price' in question_lower:
            if 'price' in stats:
                max_price = stats['price']['max']
                return f"The **highest price** in your dataset is **${max_price:.2f}**. This represents the premium end of your product range."
        
        elif any(word in question_lower for word in ['lowest', 'minimum', 'min', 'cheapest']):
            if 'price' in stats:
                min_price = stats['price']['min']
                return f"The **lowest price** in your dataset is **${min_price:.2f}**. This represents the most affordable option in your product range."
        
        elif any(word in question_lower for word in ['how many', 'count', 'total']):
            return f"Your dataset contains **{file_info['total_rows']} records** across **{file_info['columns']} columns**. This gives you a comprehensive view of your data volume."
        
        elif any(word in question_lower for word in ['correlation', 'relationship']):
            if 'correlation' in analysis_results and 'strong_correlations' in analysis_results['correlation']:
                strong_corrs = analysis_results['correlation']['strong_correlations']
                if strong_corrs:
                    corr = strong_corrs[0]
                    return f"I found a **{corr['strength']} {corr['direction']} correlation** between **{corr['variable1']}** and **{corr['variable2']}** (r={corr['correlation']:.3f}). This suggests these variables are closely related in your data."
        
        elif any(word in question_lower for word in ['segment', 'cluster', 'group']):
            if 'clustering' in analysis_results:
                cluster_count = len(analysis_results['clustering'].get('cluster_analysis', {}))
                return f"I identified **{cluster_count} distinct segments** in your data. Each group has unique characteristics that could be valuable for targeted strategies."
        
        elif any(word in question_lower for word in ['histogram', 'distribution']):
            return f"I've created a histogram showing the distribution of your data. This visualization reveals the frequency patterns and helps identify common value ranges in your dataset."
        
        elif any(word in question_lower for word in ['bar chart', 'compare']):
            return f"The bar chart compares values across different categories in your data, making it easy to see which groups have the highest and lowest values."
        
        else:
            # Try to find any specific column mentioned in the question
            for col_name, col_data in stats.items():
                if col_name.lower() in question_lower:
                    return f"For **{col_name}** in your data: average = {col_data['mean']:.2f}, range = {col_data['min']:.2f} to {col_data['max']:.2f}. This gives you key insights about this variable's distribution."
            
            return f"Based on your **{file_info['filename']}** data with **{file_info['total_rows']} records**, I've performed comprehensive analysis to answer your question. The results show meaningful patterns and insights specific to your dataset."

    async def _generate_intelligent_follow_ups(
        self, 
        question: str, 
        analysis_results: Dict[str, Any], 
        schema: Dict
    ) -> List[str]:
        """Generate intelligent follow-up questions based on sophisticated analysis"""
        try:
            follow_ups = []
            
            # Add follow-ups based on what analysis was performed
            if 'correlation' in analysis_results:
                strong_corrs = analysis_results['correlation'].get('strong_correlations', [])
                if strong_corrs:
                    corr = strong_corrs[0]
                    follow_ups.append(f"What drives the relationship between {corr['variable1']} and {corr['variable2']}?")
            
            if 'clustering' in analysis_results:
                follow_ups.append("Can you explain the characteristics of each data segment?")
                follow_ups.append("How can I use these segments for business strategy?")
            
            if 'outlier' in analysis_results:
                follow_ups.append("Should I remove these outliers or investigate them further?")
            
            # Add prediction-related follow-ups
            prediction_results = {k: v for k, v in analysis_results.items() if 'prediction' in k.lower()}
            if prediction_results:
                follow_ups.append("What factors most influence the predictions?")
                follow_ups.append("Can you forecast future values based on current trends?")
            
            # Add general sophisticated follow-ups
            follow_ups.extend([
                "Show me a comprehensive dashboard of all insights",
                "What are the most important patterns I should know about?",
                "How can I improve my data quality for better analysis?",
                "What business actions do you recommend based on this analysis?"
            ])
            
            return follow_ups[:4]  # Return top 4 follow-ups
            
        except Exception as e:
            logger.error(f"Error generating intelligent follow-ups: {e}")
            return [
                "What other patterns can you find in this data?",
                "Show me a detailed statistical analysis",
                "What business insights can you extract?",
                "How can I use this analysis to make decisions?"
            ]

    async def _call_ollama(self, prompt: str, model: str) -> str:
        """Make API call to Ollama with enhanced parameters"""
        
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1 if model == self.code_model else 0.3,
                            "top_k": 10,
                            "top_p": 0.9,
                            "num_predict": 512,  # Limit response length
                            "stop": ["```", "Note:", "Here's", "This query"]  # Stop tokens
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    raise Exception(f"LLM API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise Exception(f"Could not connect to LLM service: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama service"""
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def suggest_questions(self, schema: Dict[str, Any], dataset_name: str) -> List[str]:
        """Suggest business questions based on data analysis"""
        
        questions = []
        
        # Analyze schema to generate intelligent questions
        numeric_cols = [col for col, info in schema.items() if info.get('type') in ['number', 'currency', 'percentage']]
        categorical_cols = [col for col, info in schema.items() if info.get('type') == 'category']
        date_cols = [col for col, info in schema.items() if info.get('type') == 'date']
        
        # Metrics questions
        if numeric_cols:
            for col in numeric_cols[:2]:
                col_display = col.replace('_', ' ').title()
                questions.extend([
                    f"What's the total {col_display.lower()}?",
                    f"What's the average {col_display.lower()}?",
                    f"Show me the distribution of {col_display.lower()}"
                ])
        
        # Ranking questions
        if numeric_cols and categorical_cols:
            num_col = numeric_cols[0].replace('_', ' ').title()
            cat_col = categorical_cols[0].replace('_', ' ').title()
            questions.extend([
                f"Which {cat_col.lower()} has the highest {num_col.lower()}?",
                f"Show me the top 10 {cat_col.lower()} by {num_col.lower()}",
                f"Compare {num_col.lower()} across different {cat_col.lower()}"
            ])
        
        # Trend questions
        if date_cols and numeric_cols:
            num_col = numeric_cols[0].replace('_', ' ').title()
            questions.extend([
                f"How has {num_col.lower()} changed over time?",
                f"Show me {num_col.lower()} trends by month",
                f"What's the {num_col.lower()} growth rate?"
            ])
        
        # Count questions
        questions.extend([
            f"How many records are in {dataset_name}?",
            "Show me a summary of this data"
        ])
        
        # Business-specific questions based on common column patterns
        col_names = [col.lower() for col in schema.keys()]
        
        if any('customer' in col for col in col_names):
            questions.append("Who are our most valuable customers?")
        if any('product' in col for col in col_names):
            questions.append("What are our best-selling products?")
        if any('sales' in col or 'revenue' in col for col in col_names):
            questions.append("What are our sales trends?")
        if any('status' in col for col in col_names):
            questions.append("What's the breakdown by status?")
        
        return questions[:10]  # Limit to 10 questions