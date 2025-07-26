"""
Adaptive Query Engine
Understands business context and generates appropriate SQL queries and visualizations
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.enhanced_llm_service import EnhancedLLMService
from app.database import get_db, Dataset, Query, AsyncSessionLocal

logger = logging.getLogger(__name__)


class AdaptiveQueryEngine:
    """
    Intelligent query engine that adapts to any data structure and business context
    """
    
    def __init__(self):
        self.llm_service = EnhancedLLMService()
    
    async def process_natural_language_query(self, question: str, dataset_id: str) -> Dict[str, Any]:
        """
        Process a natural language question and return results with appropriate visualization
        """
        try:
            # 1. Get dataset context and schema
            dataset_context = await self._get_dataset_context(dataset_id)
            if not dataset_context:
                return {'error': 'Dataset not found'}
            
            # 2. Understand question intent and context
            query_intent = await self._analyze_query_intent(question, dataset_context)
            
            # 3. Generate contextually appropriate SQL
            sql_query = await self._generate_adaptive_sql(question, dataset_context, query_intent)
            
            # 4. Execute query safely
            results = await self._execute_query_safely(sql_query, dataset_context['table_name'])
            
            # 5. Generate business-friendly response
            business_answer = await self._generate_business_answer(question, results, dataset_context)
            
            # 6. Determine optimal visualization
            visualization_config = await self._determine_optimal_visualization(
                results, query_intent, dataset_context
            )
            
            # 7. Store query history
            await self._store_query_history(dataset_id, question, sql_query, results, visualization_config)
            
            return {
                'success': True,
                'question': question,
                'answer': business_answer,
                'sql': sql_query,
                'results': results,
                'visualization': visualization_config,
                'intent': query_intent
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    async def _get_dataset_context(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive dataset context for query processing
        """
        async with AsyncSessionLocal() as session:
            # Get dataset information
            result = await session.execute(
                text("SELECT * FROM datasets WHERE id = :dataset_id"),
                {"dataset_id": dataset_id}
            )
            dataset = result.fetchone()
            
            if not dataset:
                return None
            
            return {
                'id': str(dataset.id),
                'table_name': dataset.table_name,
                'display_name': dataset.display_name,
                'description': dataset.description,
                'schema': dataset.schema_definition,
                'sample_questions': dataset.sample_questions or []
            }
    
    async def _analyze_query_intent(self, question: str, dataset_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the intent and requirements of the natural language question
        """
        schema_summary = self._create_schema_summary(dataset_context['schema'])
        
        intent_prompt = f"""
        Analyze this business question and determine the query intent:
        
        Question: "{question}"
        
        Available data:
        Dataset: {dataset_context['display_name']}
        Description: {dataset_context['description']}
        Columns: {schema_summary}
        
        Determine:
        1. Query type (count, aggregate, filter, comparison, trend, distribution)
        2. Required columns
        3. Grouping requirements
        4. Time dimension (if any)
        5. Aggregation type (sum, count, average, etc.)
        6. Filters needed
        7. Best visualization type
        
        Respond in JSON format:
        {{
            "query_type": "count|aggregate|filter|comparison|trend|distribution",
            "columns_needed": ["col1", "col2"],
            "groupby_columns": ["col1"],
            "time_column": "date_col or null",
            "aggregation": "sum|count|avg|max|min|none",
            "filters": {{"column": "value"}},
            "visualization_type": "bar|line|pie|table|metric|scatter",
            "intent_summary": "Brief description of what user wants"
        }}
        """
        
        try:
            intent_response = await self.llm_service.generate_response(intent_prompt)
            # Parse JSON response
            intent_data = json.loads(intent_response.strip())
            return intent_data
        except Exception as e:
            logger.error(f"Error analyzing query intent: {str(e)}")
            # Fallback to basic intent
            return {
                "query_type": "filter",
                "columns_needed": list(dataset_context['schema'].keys())[:3],
                "groupby_columns": [],
                "time_column": None,
                "aggregation": "none",
                "filters": {},
                "visualization_type": "table",
                "intent_summary": "General data query"
            }
    
    def _create_schema_summary(self, schema: Dict[str, Any]) -> str:
        """
        Create a concise schema summary for LLM processing
        """
        summary_parts = []
        for col, info in schema.items():
            display_name = info.get('display_name', col)
            business_type = info.get('business_type', 'text')
            description = info.get('description', '')
            
            summary_parts.append(f"{display_name} ({business_type}): {description}")
        
        return "\n".join(summary_parts)
    
    async def _generate_adaptive_sql(self, question: str, dataset_context: Dict[str, Any], 
                                   intent: Dict[str, Any]) -> str:
        """
        Generate SQL query that adapts to the specific data structure and intent
        """
        table_name = dataset_context['table_name']
        schema = dataset_context['schema']
        
        sql_prompt = f"""
        Generate a PostgreSQL query to answer this business question:
        
        Question: "{question}"
        Table: {table_name}
        
        Available columns:
        {self._create_schema_summary(schema)}
        
        Query intent: {intent.get('intent_summary', 'General query')}
        Query type: {intent.get('query_type', 'filter')}
        
        Requirements:
        - Use exact column names from the schema
        - Include appropriate WHERE clauses if filters are needed
        - Use proper aggregation functions if needed
        - Limit results to reasonable numbers (use LIMIT if returning many rows)
        - Handle NULL values appropriately
        - Use proper data types and casting
        
        Return only the SQL query, no explanation:
        """
        
        try:
            sql_response = await self.llm_service.generate_sql(sql_prompt)
            # Clean up the SQL response
            sql_query = sql_response.strip()
            if sql_query.startswith('```'):
                sql_query = sql_query.split('```')[1].strip()
            if sql_query.startswith('sql'):
                sql_query = sql_query[3:].strip()
            
            # Basic SQL injection prevention
            sql_query = self._sanitize_sql(sql_query)
            
            return sql_query
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            # Fallback to simple SELECT
            columns = list(schema.keys())[:5]  # First 5 columns
            return f"SELECT {', '.join(columns)} FROM {table_name} LIMIT 10"
    
    def _sanitize_sql(self, sql: str) -> str:
        """
        Basic SQL sanitization to prevent injection attacks
        """
        # Remove dangerous keywords/patterns
        dangerous_patterns = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER',
            'EXEC', 'EXECUTE', 'TRUNCATE', 'MERGE', 'CALL'
        ]
        
        sql_upper = sql.upper()
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                raise ValueError(f"Dangerous SQL operation detected: {pattern}")
        
        return sql
    
    async def _execute_query_safely(self, sql: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query with safety measures
        """
        try:
            async with AsyncSessionLocal() as session:
                # Add safety measures
                if 'LIMIT' not in sql.upper():
                    sql += ' LIMIT 1000'  # Prevent huge result sets
                
                result = await session.execute(text(sql))
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise ValueError(f"Query execution failed: {str(e)}")
    
    async def _generate_business_answer(self, question: str, results: List[Dict[str, Any]], 
                                      dataset_context: Dict[str, Any]) -> str:
        """
        Generate a human-friendly business answer based on the results
        """
        if not results:
            return "No data found matching your criteria."
        
        # Prepare results summary for LLM
        results_summary = {
            'total_rows': len(results),
            'sample_data': results[:3] if results else [],
            'columns': list(results[0].keys()) if results else []
        }
        
        answer_prompt = f"""
        Generate a clear, business-friendly answer to this question based on the query results:
        
        Question: "{question}"
        Dataset: {dataset_context['display_name']}
        
        Results summary:
        - Total rows returned: {results_summary['total_rows']}
        - Sample data: {json.dumps(results_summary['sample_data'], default=str)}
        
        Provide a concise, informative answer that directly addresses the business question.
        Include key numbers and insights. Make it conversational and easy to understand.
        """
        
        try:
            business_answer = await self.llm_service.generate_response(answer_prompt)
            return business_answer.strip()
        except Exception as e:
            logger.error(f"Error generating business answer: {str(e)}")
            # Fallback answer
            if len(results) == 1 and len(results[0]) == 1:
                # Single value result
                value = list(results[0].values())[0]
                return f"The answer is: {value}"
            else:
                return f"Found {len(results)} records matching your criteria."
    
    async def _determine_optimal_visualization(self, results: List[Dict[str, Any]], 
                                             intent: Dict[str, Any], 
                                             dataset_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the best visualization based on data characteristics and intent
        """
        if not results:
            return {'type': 'message', 'config': {'message': 'No data to visualize'}}
        
        # Analyze result structure
        num_rows = len(results)
        num_columns = len(results[0]) if results else 0
        columns = list(results[0].keys()) if results else []
        
        # Default visualization config
        viz_config = {
            'type': 'table',
            'config': {
                'data': results,
                'columns': columns,
                'title': f"Query Results ({num_rows} rows)"
            }
        }
        
        # Determine optimal visualization based on intent and data
        suggested_viz = intent.get('visualization_type', 'table')
        
        try:
            if suggested_viz == 'metric' and num_rows == 1 and num_columns == 1:
                # Single metric value
                value = list(results[0].values())[0]
                viz_config = {
                    'type': 'metric',
                    'config': {
                        'value': value,
                        'title': columns[0].replace('_', ' ').title(),
                        'format': 'number'
                    }
                }
            
            elif suggested_viz == 'bar' and num_columns == 2:
                # Bar chart for category-value pairs
                viz_config = {
                    'type': 'bar',
                    'config': {
                        'data': results,
                        'x_column': columns[0],
                        'y_column': columns[1],
                        'title': f"{columns[1].replace('_', ' ').title()} by {columns[0].replace('_', ' ').title()}"
                    }
                }
            
            elif suggested_viz == 'pie' and num_columns == 2:
                # Pie chart for categorical distribution
                viz_config = {
                    'type': 'pie',
                    'config': {
                        'data': results,
                        'label_column': columns[0],
                        'value_column': columns[1],
                        'title': f"Distribution of {columns[1].replace('_', ' ').title()}"
                    }
                }
            
            elif suggested_viz == 'line' and num_columns >= 2:
                # Line chart for time series or trends
                viz_config = {
                    'type': 'line',
                    'config': {
                        'data': results,
                        'x_column': columns[0],
                        'y_column': columns[1],
                        'title': f"{columns[1].replace('_', ' ').title()} over {columns[0].replace('_', ' ').title()}"
                    }
                }
            
            # Add intelligent defaults based on data types
            elif num_rows <= 20 and num_columns <= 8:
                # Small dataset - keep as table
                pass
            elif num_columns == 2 and self._is_categorical_numeric_pair(results, columns):
                # Category-value pair - use bar chart
                viz_config['type'] = 'bar'
                viz_config['config'] = {
                    'data': results,
                    'x_column': columns[0],
                    'y_column': columns[1],
                    'title': f"{columns[1].replace('_', ' ').title()} by {columns[0].replace('_', ' ').title()}"
                }
        
        except Exception as e:
            logger.error(f"Error determining visualization: {str(e)}")
            # Keep default table visualization
            pass
        
        return viz_config
    
    def _is_categorical_numeric_pair(self, results: List[Dict[str, Any]], columns: List[str]) -> bool:
        """
        Check if we have a categorical-numeric column pair suitable for bar/pie charts
        """
        if len(columns) != 2:
            return False
        
        # Check if first column is categorical (string) and second is numeric
        try:
            first_col_values = [row[columns[0]] for row in results[:5]]
            second_col_values = [row[columns[1]] for row in results[:5]]
            
            # First column should be string-like (categorical)
            first_is_categorical = all(isinstance(val, (str, bool)) for val in first_col_values)
            
            # Second column should be numeric
            second_is_numeric = all(isinstance(val, (int, float)) or 
                                  (isinstance(val, str) and val.replace('.', '').isdigit())
                                  for val in second_col_values if val is not None)
            
            return first_is_categorical and second_is_numeric
        except:
            return False
    
    async def _store_query_history(self, dataset_id: str, question: str, sql: str, 
                                 results: List[Dict[str, Any]], 
                                 visualization_config: Dict[str, Any]) -> None:
        """
        Store query in history for future reference
        """
        try:
            async with AsyncSessionLocal() as session:
                query_record = Query(
                    dataset_id=dataset_id,
                    question=question,
                    generated_sql=sql,
                    results=results,
                    visualization_config=visualization_config,
                    execution_time_ms=0,  # Would measure actual execution time
                    success=True
                )
                session.add(query_record)
                await session.commit()
        except Exception as e:
            logger.error(f"Error storing query history: {str(e)}")
    
    async def get_query_suggestions(self, dataset_id: str, partial_question: str = "") -> List[str]:
        """
        Get intelligent query suggestions based on dataset and partial input
        """
        try:
            dataset_context = await self._get_dataset_context(dataset_id)
            if not dataset_context:
                return []
            
            # Start with sample questions
            suggestions = dataset_context.get('sample_questions', [])
            
            if partial_question:
                # Generate contextual suggestions based on partial input
                suggestion_prompt = f"""
                Based on this partial question and dataset, suggest 3 complete questions:
                
                Partial question: "{partial_question}"
                Dataset: {dataset_context['display_name']}
                Available columns: {list(dataset_context['schema'].keys())}
                
                Generate relevant, specific business questions that complete or extend the partial question.
                """
                
                try:
                    llm_suggestions = await self.llm_service.generate_response(suggestion_prompt)
                    new_suggestions = [s.strip() for s in llm_suggestions.split('\n') 
                                     if s.strip() and '?' in s]
                    suggestions.extend(new_suggestions[:3])
                except:
                    pass
            
            return suggestions[:8]  # Limit to 8 suggestions
            
        except Exception as e:
            logger.error(f"Error getting query suggestions: {str(e)}")
            return []