"""
LLM service for natural language processing using Ollama
Handles SQL generation and natural language responses
"""

import httpx
import json
import logging
from typing import Dict, Any, Optional, List
import re

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with local LLM via Ollama"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.chat_model = settings.OLLAMA_MODEL_CHAT
        self.code_model = settings.OLLAMA_MODEL_CODE
    
    async def generate_sql(
        self,
        question: str,
        schema: Dict[str, Any],
        table_name: str
    ) -> str:
        """Generate SQL query from natural language question"""
        
        logger.info(f"Generating SQL for question: {question}")
        
        # Create schema description
        schema_desc = self._create_schema_description(schema, table_name)
        
        # Create prompt for SQL generation
        prompt = f"""You are a SQL expert. Generate a PostgreSQL query to answer the user's question.
        
Database Schema:
{schema_desc}

Rules:
1. Use only the table and columns shown above
2. Return only the SQL query, no explanations
3. Use proper PostgreSQL syntax
4. For counting questions, use COUNT(*)
5. For status/category questions, use WHERE clauses
6. Always use double quotes around column names
7. Limit results to 100 rows unless specifically asked for more

User Question: {question}

SQL Query:"""

        try:
            # Use CodeLlama for SQL generation
            sql_query = await self._call_ollama(prompt, self.code_model)
            
            # Clean and validate SQL
            cleaned_sql = self._clean_sql(sql_query)
            
            logger.info(f"Generated SQL: {cleaned_sql}")
            return cleaned_sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            # Fallback to simple SELECT
            return f'SELECT * FROM {table_name} LIMIT 10'
    
    async def generate_answer(
        self,
        question: str,
        results: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> str:
        """Generate natural language answer from query results"""
        
        logger.info("Generating natural language answer")
        
        # Extract key information from results
        data = results.get('data', [])
        columns = results.get('columns', [])
        
        if not data:
            return "No data found matching your question."
        
        # Handle different types of questions
        if self._is_count_question(question):
            return self._generate_count_answer(question, data, results)
        elif self._is_aggregation_question(question):
            return self._generate_aggregation_answer(question, data, results)
        else:
            return self._generate_general_answer(question, data, results)
    
    def _create_schema_description(self, schema: Dict[str, Any], table_name: str) -> str:
        """Create human-readable schema description"""
        
        desc = f"Table: {table_name}\nColumns:\n"
        
        for col_name, col_info in schema.items():
            col_type = col_info.get('type', 'string')
            description = col_info.get('description', '')
            sample_values = col_info.get('sample_values', [])
            
            desc += f"- \"{col_name}\" ({col_type}): {description}"
            
            if sample_values:
                desc += f" (examples: {', '.join(map(str, sample_values[:3]))})"
            
            desc += "\n"
        
        return desc
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and validate generated SQL"""
        
        # Remove common prefixes/suffixes
        sql = sql.strip()
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        
        # Remove explanatory text (keep only the SQL part)
        lines = sql.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if (line.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')) or
                line.upper().startswith(('FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT')) or
                line.upper().startswith(('JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN')) or
                line.upper().startswith(('AND', 'OR')) or
                (sql_lines and not line.upper().startswith(('THE', 'THIS', 'HERE', 'ABOVE')))):
                sql_lines.append(line)
        
        cleaned_sql = '\n'.join(sql_lines) if sql_lines else sql
        
        # Ensure it ends with semicolon
        if not cleaned_sql.rstrip().endswith(';'):
            cleaned_sql += ';'
        
        return cleaned_sql
    
    def _is_count_question(self, question: str) -> bool:
        """Check if question is asking for a count"""
        count_keywords = ['how many', 'count', 'number of', 'total']
        return any(keyword in question.lower() for keyword in count_keywords)
    
    def _is_aggregation_question(self, question: str) -> bool:
        """Check if question is asking for aggregation"""
        agg_keywords = ['average', 'avg', 'sum', 'total', 'maximum', 'max', 'minimum', 'min']
        return any(keyword in question.lower() for keyword in agg_keywords)
    
    def _generate_count_answer(self, question: str, data: List[Dict], results: Dict) -> str:
        """Generate answer for count questions"""
        
        if len(data) == 1 and 'count' in str(data[0]).lower():
            # Single count result
            count_value = list(data[0].values())[0]
            
            # Extract what we're counting from the question
            if 'active' in question.lower():
                return f"You have **{count_value} active users**."
            elif 'inactive' in question.lower():
                return f"You have **{count_value} inactive users**."
            elif 'premium' in question.lower():
                return f"You have **{count_value} premium users**."
            elif 'user' in question.lower():
                return f"You have **{count_value} users** in total."
            else:
                return f"The count is **{count_value}**."
        else:
            # Multiple results - show breakdown
            total = len(data)
            return f"Found **{total} records** matching your criteria."
    
    def _generate_aggregation_answer(self, question: str, data: List[Dict], results: Dict) -> str:
        """Generate answer for aggregation questions"""
        
        if not data or not data[0]:
            return "No data available for this calculation."
        
        # Extract the aggregated value
        first_row = data[0]
        agg_value = list(first_row.values())[0]
        
        if 'average' in question.lower() or 'avg' in question.lower():
            if 'spending' in question.lower() or 'amount' in question.lower():
                return f"The average spending is **${agg_value:.2f}**."
            else:
                return f"The average value is **{agg_value}**."
        elif 'sum' in question.lower() or 'total' in question.lower():
            return f"The total is **{agg_value}**."
        elif 'max' in question.lower() or 'maximum' in question.lower():
            return f"The maximum value is **{agg_value}**."
        elif 'min' in question.lower() or 'minimum' in question.lower():
            return f"The minimum value is **{agg_value}**."
        else:
            return f"The result is **{agg_value}**."
    
    def _generate_general_answer(self, question: str, data: List[Dict], results: Dict) -> str:
        """Generate answer for general questions"""
        
        record_count = len(data)
        
        if record_count == 0:
            return "No records found matching your criteria."
        elif record_count == 1:
            return f"Found 1 record matching your criteria."
        else:
            return f"Found **{record_count} records** matching your criteria. The data shows various insights based on your query."
    
    async def _call_ollama(self, prompt: str, model: str) -> str:
        """Make API call to Ollama"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for consistent SQL
                            "top_k": 10,
                            "top_p": 0.9
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