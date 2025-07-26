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
        """Extract business entities from the question"""
        
        question_lower = question.lower()
        entities = {
            "columns": [],
            "values": [],
            "time_periods": [],
            "aggregations": [],
            "filters": []
        }
        
        # Extract column references
        for col_name, col_info in schema.items():
            col_variations = [
                col_name,
                col_name.replace('_', ' '),
                col_name.replace('_', ''),
                col_info.get('description', '').lower()
            ]
            
            for variation in col_variations:
                if variation and variation.lower() in question_lower:
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

BUSINESS RULES:
1. Always use meaningful column aliases that business users understand
2. Format numbers appropriately (currency as currency, percentages as percentages)
3. Include relevant sorting for business insights
4. Limit results to reasonable business ranges (e.g., top 10, last 100 records)
5. Use proper date formatting for time-based analysis
6. Always use double quotes around column names
7. Return only the SQL query, no explanations

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
        
        # Generate answer based on business intent
        if intent_analysis['primary_intent'] == 'metrics':
            return self._generate_metrics_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'rankings':
            return self._generate_ranking_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'trends':
            return self._generate_trend_answer(question, data, intent_analysis)
        elif intent_analysis['primary_intent'] == 'comparisons':
            return self._generate_comparison_answer(question, data, intent_analysis)
        else:
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
    
    def _generate_metrics_answer(self, question: str, data: List[Dict], intent_analysis: Dict[str, Any]) -> str:
        """Generate answer for metrics questions"""
        
        if len(data) == 1:
            result = data[0]
            value = list(result.values())[0]
            
            # Format based on the question type
            question_lower = question.lower()
            
            if 'count' in question_lower or 'how many' in question_lower:
                return f"**{value:,}** records match your criteria."
            elif 'total' in question_lower or 'sum' in question_lower:
                if isinstance(value, (int, float)):
                    return f"The total is **${value:,.2f}**." if 'amount' in question_lower or 'revenue' in question_lower else f"The total is **{value:,}**."
            elif 'average' in question_lower or 'avg' in question_lower:
                if isinstance(value, (int, float)):
                    return f"The average is **${value:,.2f}**." if 'amount' in question_lower or 'revenue' in question_lower else f"The average is **{value:.2f}**."
            
            return f"The result is **{value}**."
        
        return f"Found **{len(data)}** metric results."
    
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
        """Generate answer for general questions"""
        
        count = len(data)
        
        if count == 1:
            return "Found **1 record** that matches your question."
        else:
            return f"Found **{count} records** that provide insights for your question."
    
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