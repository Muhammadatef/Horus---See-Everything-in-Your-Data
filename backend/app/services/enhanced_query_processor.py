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
            
            schema = data_source.schema_info or {}
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
            
            # Step 3: Generate natural language answer
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


# Global instance
enhanced_query_processor = EnhancedQueryProcessor()