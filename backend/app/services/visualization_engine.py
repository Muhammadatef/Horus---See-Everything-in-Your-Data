"""
Modern Visualization Engine for Local AI-BI Platform
Auto-generates appropriate charts based on data types and query intent
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class VisualizationEngine:
    """Intelligent visualization engine that auto-selects appropriate chart types"""
    
    def __init__(self):
        self.chart_themes = {
            "default": {
                "colorScheme": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c", "#34495e"],
                "backgroundColor": "#ffffff",
                "textColor": "#2c3e50",
                "gridColor": "#ecf0f1"
            },
            "dark": {
                "colorScheme": ["#5dade2", "#ec7063", "#58d68d", "#f7dc6f", "#bb8fce", "#76d7c4", "#85929e"],
                "backgroundColor": "#2c3e50",
                "textColor": "#ecf0f1",
                "gridColor": "#34495e"
            }
        }
    
    async def generate_visualization(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        question: str,
        schema: Dict[str, Any],
        intent_type: str = "general"
    ) -> Dict[str, Any]:
        """Generate appropriate visualization based on data and query intent"""
        
        if not data or not columns:
            return self._create_empty_chart()
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        
        # Analyze data characteristics
        data_analysis = self._analyze_data_characteristics(df, schema)
        
        # Determine best visualization type
        chart_type = self._select_chart_type(
            data_analysis, question, intent_type, len(df), len(columns)
        )
        
        # Generate chart configuration
        chart_config = await self._generate_chart_config(
            df, chart_type, data_analysis, question
        )
        
        # Add insights and summary
        insights = self._generate_chart_insights(df, chart_type, data_analysis)
        
        return {
            "type": chart_type,
            "config": chart_config,
            "insights": insights,
            "data_summary": {
                "rows": len(df),
                "columns": len(df.columns),
                "chart_type": chart_type,
                "recommended_actions": self._get_recommended_actions(chart_type, data_analysis)
            }
        }
    
    def _analyze_data_characteristics(self, df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data to determine visualization characteristics"""
        
        analysis = {
            "numeric_columns": [],
            "categorical_columns": [],
            "date_columns": [],
            "boolean_columns": [],
            "data_patterns": [],
            "value_distributions": {},
            "has_time_series": False,
            "cardinality": {}
        }
        
        for col in df.columns:
            col_info = schema.get(col, {})
            col_type = col_info.get('type', 'unknown')
            unique_count = df[col].nunique()
            
            analysis["cardinality"][col] = unique_count
            
            if col_type in ['number', 'currency', 'percentage']:
                analysis["numeric_columns"].append(col)
            elif col_type in ['category', 'text']:
                if unique_count <= 20:  # Reasonable for categorical visualization
                    analysis["categorical_columns"].append(col)
            elif col_type == 'date':
                analysis["date_columns"].append(col)
                analysis["has_time_series"] = True
            elif col_type == 'boolean':
                analysis["boolean_columns"].append(col)
            
            # Analyze value distribution
            if unique_count <= 50:  # For manageable visualization
                value_counts = df[col].value_counts().head(10)
                analysis["value_distributions"][col] = value_counts.to_dict()
        
        # Detect patterns
        if len(analysis["numeric_columns"]) >= 2:
            analysis["data_patterns"].append("correlation_analysis")
        
        if len(analysis["categorical_columns"]) >= 1 and len(analysis["numeric_columns"]) >= 1:
            analysis["data_patterns"].append("category_breakdown")
        
        if analysis["has_time_series"] and len(analysis["numeric_columns"]) >= 1:
            analysis["data_patterns"].append("time_series")
        
        return analysis
    
    def _select_chart_type(
        self,
        analysis: Dict[str, Any],
        question: str,
        intent_type: str,
        row_count: int,
        col_count: int
    ) -> str:
        """Select the most appropriate chart type"""
        
        question_lower = question.lower()
        numeric_cols = len(analysis["numeric_columns"])
        categorical_cols = len(analysis["categorical_columns"])
        
        # Priority 1: Question intent keywords
        if any(word in question_lower for word in ['trend', 'over time', 'timeline', 'historical']):
            if analysis["has_time_series"]:
                return "line_chart"
        
        if any(word in question_lower for word in ['distribution', 'spread', 'histogram']):
            if numeric_cols >= 1:
                return "histogram"
        
        if any(word in question_lower for word in ['compare', 'comparison', 'vs', 'versus']):
            if categorical_cols >= 1:
                return "bar_chart"
        
        if any(word in question_lower for word in ['percentage', 'proportion', 'share', 'breakdown']):
            if categorical_cols >= 1:
                return "pie_chart"
        
        if any(word in question_lower for word in ['correlation', 'relationship', 'scatter']):
            if numeric_cols >= 2:
                return "scatter_plot"
        
        # Priority 2: Data patterns
        if intent_type == "count" and categorical_cols >= 1:
            return "bar_chart"
        
        if intent_type == "aggregation" and row_count == 1:
            return "metric_card"
        
        # Priority 3: Data structure analysis
        if row_count == 1 and col_count == 1:
            return "metric_card"
        
        if analysis["has_time_series"] and numeric_cols >= 1:
            return "line_chart"
        
        if categorical_cols >= 1 and numeric_cols >= 1:
            unique_categories = min([analysis["cardinality"][col] for col in analysis["categorical_columns"]])
            if unique_categories <= 10:
                return "bar_chart"
        
        if categorical_cols >= 1 and row_count <= 10:
            return "pie_chart"
        
        if numeric_cols >= 2:
            return "scatter_plot"
        
        if numeric_cols == 1:
            return "histogram"
        
        # Default fallback
        if row_count <= 100:
            return "data_table"
        else:
            return "metric_card"
    
    async def _generate_chart_config(
        self,
        df: pd.DataFrame,
        chart_type: str,
        analysis: Dict[str, Any],
        question: str
    ) -> Dict[str, Any]:
        """Generate ECharts configuration based on chart type"""
        
        theme = self.chart_themes["default"]
        
        if chart_type == "metric_card":
            return self._generate_metric_card(df, theme)
        elif chart_type == "bar_chart":
            return self._generate_bar_chart(df, analysis, theme, question)
        elif chart_type == "pie_chart":
            return self._generate_pie_chart(df, analysis, theme)
        elif chart_type == "line_chart":
            return self._generate_line_chart(df, analysis, theme)
        elif chart_type == "scatter_plot":
            return self._generate_scatter_plot(df, analysis, theme)
        elif chart_type == "histogram":
            return self._generate_histogram(df, analysis, theme)
        elif chart_type == "data_table":
            return self._generate_data_table(df, theme)
        else:
            return self._generate_bar_chart(df, analysis, theme, question)
    
    def _generate_metric_card(self, df: pd.DataFrame, theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metric card configuration"""
        
        if len(df) == 1 and len(df.columns) == 1:
            value = df.iloc[0, 0]
            column_name = df.columns[0]
        else:
            # Find the most relevant metric
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                value = df[numeric_cols[0]].iloc[0] if len(df) > 0 else 0
                column_name = numeric_cols[0]
            else:
                value = len(df)
                column_name = "Total Records"
        
        return {
            "type": "metric",
            "data": {
                "value": value,
                "title": column_name.replace('_', ' ').title(),
                "format": self._determine_number_format(value),
                "color": theme["colorScheme"][0]
            }
        }
    
    def _generate_bar_chart(self, df: pd.DataFrame, analysis: Dict[str, Any], theme: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Generate bar chart configuration"""
        
        # Find best categorical and numeric columns
        cat_col = analysis["categorical_columns"][0] if analysis["categorical_columns"] else df.columns[0]
        
        if len(analysis["numeric_columns"]) > 0:
            num_col = analysis["numeric_columns"][0]
            
            # Group by categorical column and aggregate numeric
            grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(20)
            categories = grouped.index.tolist()
            values = grouped.values.tolist()
            
        else:
            # Count occurrences
            value_counts = df[cat_col].value_counts().head(20)
            categories = value_counts.index.tolist()
            values = value_counts.values.tolist()
            num_col = "Count"
        
        return {
            "title": {
                "text": f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                "left": "center",
                "textStyle": {"color": theme["textColor"]}
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"}
            },
            "xAxis": {
                "type": "category",
                "data": categories,
                "axisLabel": {
                    "rotate": 45 if len(max(categories, key=len)) > 10 else 0,
                    "color": theme["textColor"]
                }
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": theme["textColor"]}
            },
            "series": [{
                "name": num_col.replace('_', ' ').title(),
                "type": "bar",
                "data": values,
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": theme["colorScheme"][0]},
                            {"offset": 1, "color": theme["colorScheme"][1]}
                        ]
                    }
                },
                "emphasis": {
                    "itemStyle": {"color": theme["colorScheme"][2]}
                }
            }],
            "backgroundColor": theme["backgroundColor"]
        }
    
    def _generate_pie_chart(self, df: pd.DataFrame, analysis: Dict[str, Any], theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pie chart configuration"""
        
        cat_col = analysis["categorical_columns"][0] if analysis["categorical_columns"] else df.columns[0]
        
        if len(analysis["numeric_columns"]) > 0:
            num_col = analysis["numeric_columns"][0]
            grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
            data = [{"name": str(name), "value": float(value)} for name, value in grouped.items()]
        else:
            value_counts = df[cat_col].value_counts().head(10)
            data = [{"name": str(name), "value": int(value)} for name, value in value_counts.items()]
        
        return {
            "title": {
                "text": f"Distribution of {cat_col.replace('_', ' ').title()}",
                "left": "center",
                "textStyle": {"color": theme["textColor"]}
            },
            "tooltip": {
                "trigger": "item",
                "formatter": "{a} <br/>{b}: {c} ({d}%)"
            },
            "legend": {
                "orient": "vertical",
                "left": "left",
                "textStyle": {"color": theme["textColor"]}
            },
            "series": [{
                "name": cat_col.replace('_', ' ').title(),
                "type": "pie",
                "radius": "50%",
                "data": data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                },
                "itemStyle": {
                    "color": lambda params: theme["colorScheme"][params["dataIndex"] % len(theme["colorScheme"])]
                }
            }],
            "backgroundColor": theme["backgroundColor"]
        }
    
    def _generate_line_chart(self, df: pd.DataFrame, analysis: Dict[str, Any], theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate line chart configuration"""
        
        date_col = analysis["date_columns"][0] if analysis["date_columns"] else df.columns[0]
        
        # Sort by date
        df_sorted = df.sort_values(date_col)
        
        series_data = []
        
        for num_col in analysis["numeric_columns"][:3]:  # Max 3 lines
            series_data.append({
                "name": num_col.replace('_', ' ').title(),
                "type": "line",
                "data": df_sorted[num_col].tolist(),
                "smooth": True,
                "lineStyle": {"width": 2},
                "itemStyle": {"color": theme["colorScheme"][len(series_data)]}
            })
        
        return {
            "title": {
                "text": f"Trends Over Time",
                "left": "center",
                "textStyle": {"color": theme["textColor"]}
            },
            "tooltip": {
                "trigger": "axis"
            },
            "legend": {
                "data": [s["name"] for s in series_data],
                "textStyle": {"color": theme["textColor"]}
            },
            "xAxis": {
                "type": "category",
                "data": df_sorted[date_col].astype(str).tolist(),
                "axisLabel": {"color": theme["textColor"]}
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": theme["textColor"]}
            },
            "series": series_data,
            "backgroundColor": theme["backgroundColor"]
        }
    
    def _generate_scatter_plot(self, df: pd.DataFrame, analysis: Dict[str, Any], theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scatter plot configuration"""
        
        num_cols = analysis["numeric_columns"][:2]
        if len(num_cols) < 2:
            return self._generate_bar_chart(df, analysis, theme, "")
        
        x_col, y_col = num_cols[0], num_cols[1]
        
        data = [[float(row[x_col]), float(row[y_col])] for _, row in df.iterrows() 
                if pd.notna(row[x_col]) and pd.notna(row[y_col])]
        
        return {
            "title": {
                "text": f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}",
                "left": "center",
                "textStyle": {"color": theme["textColor"]}
            },
            "tooltip": {
                "trigger": "item",
                "formatter": f"{x_col}: {{c[0]}}<br/>{y_col}: {{c[1]}}"
            },
            "xAxis": {
                "name": x_col.replace('_', ' ').title(),
                "axisLabel": {"color": theme["textColor"]}
            },
            "yAxis": {
                "name": y_col.replace('_', ' ').title(),
                "axisLabel": {"color": theme["textColor"]}
            },
            "series": [{
                "type": "scatter",
                "data": data,
                "itemStyle": {
                    "color": theme["colorScheme"][0],
                    "opacity": 0.7
                },
                "emphasis": {
                    "itemStyle": {"color": theme["colorScheme"][1]}
                }
            }],
            "backgroundColor": theme["backgroundColor"]
        }
    
    def _generate_histogram(self, df: pd.DataFrame, analysis: Dict[str, Any], theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate histogram configuration"""
        
        num_col = analysis["numeric_columns"][0] if analysis["numeric_columns"] else df.columns[0]
        
        # Create bins
        values = df[num_col].dropna()
        hist, bin_edges = np.histogram(values, bins=min(20, len(values) // 5 + 1))
        
        categories = [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(len(hist))]
        
        return {
            "title": {
                "text": f"Distribution of {num_col.replace('_', ' ').title()}",
                "left": "center",
                "textStyle": {"color": theme["textColor"]}
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"}
            },
            "xAxis": {
                "type": "category",
                "data": categories,
                "axisLabel": {
                    "rotate": 45,
                    "color": theme["textColor"]
                }
            },
            "yAxis": {
                "type": "value",
                "name": "Frequency",
                "axisLabel": {"color": theme["textColor"]}
            },
            "series": [{
                "name": "Frequency",
                "type": "bar",
                "data": hist.tolist(),
                "itemStyle": {
                    "color": theme["colorScheme"][0]
                }
            }],
            "backgroundColor": theme["backgroundColor"]
        }
    
    def _generate_data_table(self, df: pd.DataFrame, theme: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data table configuration"""
        
        # Limit to first 100 rows and format data
        df_display = df.head(100)
        
        return {
            "type": "table",
            "columns": [{"title": col.replace('_', ' ').title(), "key": col} for col in df_display.columns],
            "data": df_display.to_dict('records'),
            "pagination": {
                "pageSize": 20,
                "showSizeChanger": True,
                "showQuickJumper": True
            },
            "scroll": {"x": True, "y": 400}
        }
    
    def _create_empty_chart(self) -> Dict[str, Any]:
        """Create empty chart for no data scenarios"""
        
        return {
            "type": "empty",
            "config": {
                "title": {
                    "text": "No Data Available",
                    "left": "center",
                    "top": "center",
                    "textStyle": {"color": "#999", "fontSize": 18}
                }
            },
            "insights": ["No data available for visualization"],
            "data_summary": {
                "rows": 0,
                "columns": 0,
                "chart_type": "empty",
                "recommended_actions": ["Upload data or refine your query"]
            }
        }
    
    def _generate_chart_insights(self, df: pd.DataFrame, chart_type: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about the visualization"""
        
        insights = []
        
        if chart_type == "metric_card":
            insights.append("Single value metric displayed prominently")
        
        elif chart_type == "bar_chart":
            if analysis["categorical_columns"]:
                cat_col = analysis["categorical_columns"][0]
                top_category = df[cat_col].value_counts().index[0]
                insights.append(f"'{top_category}' is the most frequent category")
        
        elif chart_type == "pie_chart":
            insights.append("Shows proportional breakdown of categories")
            total_categories = len(analysis.get("value_distributions", {}).get(analysis["categorical_columns"][0], {}))
            if total_categories > 10:
                insights.append(f"Showing top 10 out of {total_categories} categories")
        
        elif chart_type == "line_chart":
            insights.append("Time series data shows trends over time")
            if len(analysis["numeric_columns"]) > 1:
                insights.append("Multiple metrics can be compared across time")
        
        elif chart_type == "scatter_plot":
            insights.append("Shows relationship between two numeric variables")
            
        elif chart_type == "histogram":
            insights.append("Shows distribution pattern of numeric values")
        
        # Add data quality insights
        missing_data = df.isnull().sum().sum()
        if missing_data > 0:
            insights.append(f"Note: {missing_data} missing values in the dataset")
        
        return insights
    
    def _get_recommended_actions(self, chart_type: str, analysis: Dict[str, Any]) -> List[str]:
        """Get recommended actions for the user"""
        
        actions = []
        
        if chart_type == "data_table":
            actions.append("Consider filtering the data for better visualization")
            actions.append("Try asking about specific aspects of the data")
        
        elif len(analysis["numeric_columns"]) > 0 and len(analysis["categorical_columns"]) > 0:
            actions.append("Try comparing numeric values across categories")
            actions.append("Ask about averages, totals, or distributions")
        
        if analysis["has_time_series"]:
            actions.append("Explore trends over time")
            actions.append("Ask about patterns or changes in the data")
        
        if len(analysis["numeric_columns"]) >= 2:
            actions.append("Explore correlations between numeric variables")
        
        return actions[:3]  # Limit to 3 recommendations
    
    def _determine_number_format(self, value: Any) -> str:
        """Determine appropriate number format"""
        
        if isinstance(value, (int, float)):
            if abs(value) >= 1000000:
                return "million"
            elif abs(value) >= 1000:
                return "thousand"
            elif isinstance(value, float) and value % 1 != 0:
                return "decimal"
        
        return "integer"


# Global visualization engine instance
visualization_engine = VisualizationEngine()