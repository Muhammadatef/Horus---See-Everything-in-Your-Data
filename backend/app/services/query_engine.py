"""
Query execution and visualization service
Handles SQL execution and chart generation
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


class QueryEngine:
    """Service for executing queries and generating visualizations"""
    
    async def execute_query(self, sql: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute SQL query and return structured results"""
        
        logger.info(f"Executing query: {sql}")
        
        try:
            # Execute query
            result = await db.execute(text(sql))
            rows = result.fetchall()
            
            if not rows:
                return {
                    "columns": [],
                    "data": [],
                    "row_count": 0
                }
            
            # Get column names
            columns = list(rows[0]._fields)
            
            # Convert rows to list of dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Handle different data types
                    if hasattr(value, 'isoformat'):  # datetime
                        row_dict[col] = value.isoformat()
                    elif isinstance(value, (int, float, str, bool)):
                        row_dict[col] = value
                    elif value is None:
                        row_dict[col] = None
                    else:
                        row_dict[col] = str(value)
                data.append(row_dict)
            
            logger.info(f"Query returned {len(data)} rows")
            
            return {
                "columns": columns,
                "data": data,
                "row_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise Exception(f"Query execution failed: {str(e)}")
    
    async def suggest_visualization(
        self,
        results: Dict[str, Any],
        question: str,
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Suggest appropriate visualization based on query results"""
        
        data = results.get("data", [])
        columns = results.get("columns", [])
        
        if not data or not columns:
            return None
        
        # Analyze data characteristics
        viz_config = self._analyze_and_suggest_chart(data, columns, question, schema)
        
        logger.info(f"Suggested visualization: {viz_config.get('type', 'table')}")
        
        return viz_config
    
    def _analyze_and_suggest_chart(
        self,
        data: List[Dict],
        columns: List[str],
        question: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data and suggest the best chart type"""
        
        num_columns = len(columns)
        num_rows = len(data)
        question_lower = question.lower()
        
        # Single value result (aggregations, counts)
        if num_rows == 1 and num_columns == 1:
            value = list(data[0].values())[0]
            
            if self._is_count_question(question):
                # For count questions, create a simple metric card
                return {
                    "type": "metric",
                    "title": self._extract_metric_title(question),
                    "value": value,
                    "format": "number",
                    "description": f"Result for: {question}"
                }
            elif self._is_aggregation_question(question):
                # For aggregation questions
                format_type = "currency" if "spending" in question_lower or "amount" in question_lower else "number"
                return {
                    "type": "metric",
                    "title": self._extract_metric_title(question),
                    "value": value,
                    "format": format_type,
                    "description": f"Result for: {question}"
                }
        
        # Two columns - usually good for bar charts or pie charts
        elif num_columns == 2:
            col1, col2 = columns
            
            # Check if one column is categorical and other is numeric
            first_col_data = [row.get(col1) for row in data]
            second_col_data = [row.get(col2) for row in data]
            
            first_is_numeric = self._is_numeric_data(first_col_data)
            second_is_numeric = self._is_numeric_data(second_col_data)
            
            if not first_is_numeric and second_is_numeric:
                # Category vs Number - good for bar chart or pie chart
                unique_categories = len(set(first_col_data))
                
                if unique_categories <= 8 and ("distribution" in question_lower or "breakdown" in question_lower):
                    # Pie chart for distributions with few categories
                    return {
                        "type": "pie",
                        "title": f"{col1.replace('_', ' ').title()} Distribution",
                        "data": data,
                        "category_column": col1,
                        "value_column": col2,
                        "description": f"Distribution of {col1.replace('_', ' ')}"
                    }
                else:
                    # Bar chart for comparisons
                    return {
                        "type": "bar",
                        "title": f"{col2.replace('_', ' ').title()} by {col1.replace('_', ' ').title()}",
                        "data": data,
                        "x_column": col1,
                        "y_column": col2,
                        "description": f"Comparison of {col2.replace('_', ' ')} across {col1.replace('_', ' ')}"
                    }
            
            elif first_is_numeric and not second_is_numeric:
                # Number vs Category - bar chart with swapped axes
                return {
                    "type": "bar",
                    "title": f"{col1.replace('_', ' ').title()} by {col2.replace('_', ' ').title()}",
                    "data": data,
                    "x_column": col2,
                    "y_column": col1,
                    "description": f"Comparison of {col1.replace('_', ' ')} across {col2.replace('_', ' ')}"
                }
            
            elif first_is_numeric and second_is_numeric:
                # Both numeric - scatter plot
                return {
                    "type": "scatter",
                    "title": f"{col2.replace('_', ' ').title()} vs {col1.replace('_', ' ').title()}",
                    "data": data,
                    "x_column": col1,
                    "y_column": col2,
                    "description": f"Relationship between {col1.replace('_', ' ')} and {col2.replace('_', ' ')}"
                }
        
        # Time series data
        elif self._has_date_column(columns, schema):
            date_col = self._find_date_column(columns, schema)
            numeric_cols = [col for col in columns if col != date_col and self._is_numeric_column(col, data)]
            
            if numeric_cols:
                return {
                    "type": "line",
                    "title": f"{numeric_cols[0].replace('_', ' ').title()} Over Time",
                    "data": data,
                    "x_column": date_col,
                    "y_column": numeric_cols[0],
                    "description": f"Trend of {numeric_cols[0].replace('_', ' ')} over time"
                }
        
        # Multiple columns - default to table
        return {
            "type": "table",
            "title": "Query Results",
            "data": data,
            "columns": columns,
            "description": f"Detailed results for: {question}"
        }
    
    def _is_count_question(self, question: str) -> bool:
        """Check if question is asking for a count"""
        count_keywords = ['how many', 'count', 'number of', 'total']
        return any(keyword in question.lower() for keyword in count_keywords)
    
    def _is_aggregation_question(self, question: str) -> bool:
        """Check if question is asking for aggregation"""
        agg_keywords = ['average', 'avg', 'sum', 'total', 'maximum', 'max', 'minimum', 'min']
        return any(keyword in question.lower() for keyword in agg_keywords)
    
    def _extract_metric_title(self, question: str) -> str:
        """Extract a good title for metric visualization"""
        question_lower = question.lower()
        
        if 'active users' in question_lower:
            return "Active Users"
        elif 'inactive users' in question_lower:
            return "Inactive Users"
        elif 'premium users' in question_lower:
            return "Premium Users"
        elif 'users' in question_lower:
            return "Total Users"
        elif 'average spending' in question_lower:
            return "Average Spending"
        elif 'total spending' in question_lower:
            return "Total Spending"
        else:
            return "Result"
    
    def _is_numeric_data(self, data_list: List) -> bool:
        """Check if a list of data is primarily numeric"""
        if not data_list:
            return False
        
        numeric_count = 0
        for item in data_list[:10]:  # Check first 10 items
            if isinstance(item, (int, float)) and item is not None:
                numeric_count += 1
        
        return numeric_count > len(data_list[:10]) * 0.7  # 70% threshold
    
    def _is_numeric_column(self, column: str, data: List[Dict]) -> bool:
        """Check if a column contains numeric data"""
        if not data:
            return False
        
        sample_values = [row.get(column) for row in data[:10]]
        return self._is_numeric_data(sample_values)
    
    def _has_date_column(self, columns: List[str], schema: Dict[str, Any]) -> bool:
        """Check if any column is a date type"""
        for col in columns:
            if schema.get(col, {}).get('type') == 'date':
                return True
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                return True
        return False
    
    def _find_date_column(self, columns: List[str], schema: Dict[str, Any]) -> Optional[str]:
        """Find the first date column"""
        for col in columns:
            if schema.get(col, {}).get('type') == 'date':
                return col
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                return col
        return None