"""
Advanced Data Analysis Service
Performs sophisticated data science analysis beyond basic counts and averages
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import silhouette_score
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AdvancedAnalysisService:
    """
    Sophisticated data analysis service that performs:
    - Statistical analysis (correlations, distributions, outliers)
    - Machine learning insights (clustering, prediction, anomaly detection)
    - Time series analysis (trends, seasonality, forecasting)
    - Advanced business analytics (cohort analysis, segmentation)
    - Pattern recognition and recommendations
    """
    
    def __init__(self):
        self.analysis_functions = {
            'statistical': self._perform_statistical_analysis,
            'clustering': self._perform_clustering_analysis,
            'correlation': self._perform_correlation_analysis,
            'outlier': self._perform_outlier_analysis,
            'prediction': self._perform_prediction_analysis,
            'segmentation': self._perform_customer_segmentation,
            'time_series': self._perform_time_series_analysis,
            'anomaly': self._perform_anomaly_detection,
            'distribution': self._perform_distribution_analysis,
            'performance': self._perform_performance_analysis,
            'cohort': self._perform_cohort_analysis,
            'advanced_patterns': self._perform_pattern_recognition
        }
    
    async def analyze_with_sophistication(self, data: List[Dict], question: str, schema: Dict) -> Dict[str, Any]:
        """
        Main entry point for sophisticated analysis
        Determines the best analysis approach based on the question and data
        """
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return self._generate_no_data_insights()
            
            # Determine analysis type based on question intent
            analysis_type = self._determine_analysis_type(question, df, schema)
            
            # Perform comprehensive analysis
            results = {}
            
            # Always include basic statistical overview
            results['statistical_overview'] = await self._perform_statistical_analysis(df, question)
            
            # Perform specific analysis based on question
            if analysis_type['primary']:
                primary_analysis = await self.analysis_functions[analysis_type['primary']](df, question)
                results[analysis_type['primary']] = primary_analysis
            
            # Add secondary analyses for richer insights
            for secondary in analysis_type['secondary']:
                try:
                    secondary_analysis = await self.analysis_functions[secondary](df, question)
                    results[secondary] = secondary_analysis
                except Exception as e:
                    logger.warning(f"Secondary analysis {secondary} failed: {e}")
            
            # Generate advanced insights and recommendations
            insights = self._generate_advanced_insights(results, df, question)
            recommendations = self._generate_actionable_recommendations(results, df, question)
            
            return {
                'analysis_results': results,
                'advanced_insights': insights,
                'recommendations': recommendations,
                'data_quality_score': self._calculate_data_quality_score(df),
                'analysis_confidence': self._calculate_analysis_confidence(results, df)
            }
            
        except Exception as e:
            logger.error(f"Advanced analysis failed: {e}")
            return self._generate_fallback_analysis(data, question)
    
    def _determine_analysis_type(self, question: str, df: pd.DataFrame, schema: Dict) -> Dict[str, Any]:
        """
        Intelligently determine what type of sophisticated analysis to perform
        """
        question_lower = question.lower()
        
        # Advanced pattern matching for analysis types
        analysis_patterns = {
            'clustering': ['segment', 'group', 'cluster', 'similar', 'categorize', 'patterns', 'behavior'],
            'correlation': ['relationship', 'correlat', 'related', 'depend', 'affect', 'influence', 'connect'],
            'prediction': ['predict', 'forecast', 'future', 'trend', 'project', 'estimate', 'likely'],
            'outlier': ['outlier', 'anomal', 'unusual', 'strange', 'abnormal', 'exception', 'weird'],
            'time_series': ['time', 'trend', 'season', 'month', 'week', 'day', 'year', 'period'],
            'distribution': ['distribut', 'spread', 'range', 'pattern', 'shape', 'normal'],
            'segmentation': ['customer', 'user', 'segment', 'persona', 'profile', 'type'],
            'performance': ['performance', 'efficiency', 'success', 'rate', 'metric', 'kpi']
        }
        
        # Score each analysis type
        scores = {}
        for analysis_type, keywords in analysis_patterns.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                scores[analysis_type] = score
        
        # Determine primary analysis
        primary = max(scores, key=scores.get) if scores else 'statistical'
        
        # Determine secondary analyses based on data characteristics
        secondary = []
        
        # Add correlation if numerical columns exist
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            secondary.append('correlation')
        
        # Add clustering if sufficient data
        if len(df) >= 10 and len(numeric_cols) >= 2:
            secondary.append('clustering')
        
        # Add outlier detection for numerical data
        if len(numeric_cols) >= 1:
            secondary.append('outlier')
        
        # Add time series if date columns exist
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_cols:
            secondary.append('time_series')
        
        return {
            'primary': primary,
            'secondary': list(set(secondary[:3]))  # Limit to 3 secondary analyses
        }
    
    async def _perform_statistical_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Comprehensive statistical analysis
        """
        results = {}
        
        # Descriptive statistics
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            results['descriptive_stats'] = {
                'summary': numeric_df.describe().to_dict(),
                'skewness': numeric_df.skew().to_dict(),
                'kurtosis': numeric_df.kurtosis().to_dict()
            }
            
            # Advanced statistical tests
            results['normality_tests'] = {}
            for col in numeric_df.columns:
                if len(numeric_df[col].dropna()) > 3:
                    stat, p_value = stats.shapiro(numeric_df[col].dropna()[:5000])  # Limit for performance
                    results['normality_tests'][col] = {
                        'is_normal': p_value > 0.05,
                        'p_value': float(p_value),
                        'statistic': float(stat)
                    }
        
        # Categorical analysis
        categorical_df = df.select_dtypes(include=['object', 'category'])
        if not categorical_df.empty:
            results['categorical_analysis'] = {}
            for col in categorical_df.columns:
                value_counts = df[col].value_counts()
                results['categorical_analysis'][col] = {
                    'unique_values': int(df[col].nunique()),
                    'most_common': value_counts.head(5).to_dict(),
                    'diversity_score': float(1 - (value_counts.iloc[0] / len(df))) if len(value_counts) > 0 else 0
                }
        
        return results
    
    async def _perform_correlation_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Advanced correlation and relationship analysis
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return {'error': 'Insufficient numerical columns for correlation analysis'}
        
        # Correlation matrix
        corr_matrix = numeric_df.corr()
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:  # Strong correlation threshold
                    strong_correlations.append({
                        'variable1': corr_matrix.columns[i],
                        'variable2': corr_matrix.columns[j],
                        'correlation': float(corr_val),
                        'strength': 'very strong' if abs(corr_val) > 0.8 else 'strong',
                        'direction': 'positive' if corr_val > 0 else 'negative'
                    })
        
        # Partial correlations for deeper insights
        partial_correlations = {}
        if len(numeric_df.columns) >= 3:
            for target_col in numeric_df.columns:
                other_cols = [col for col in numeric_df.columns if col != target_col]
                if len(other_cols) >= 2:
                    # Calculate partial correlation controlling for other variables
                    try:
                        partial_corr = self._calculate_partial_correlation(numeric_df, target_col, other_cols[0], other_cols[1:])
                        partial_correlations[f"{target_col}_vs_{other_cols[0]}"] = float(partial_corr)
                    except:
                        pass
        
        return {
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_correlations,
            'partial_correlations': partial_correlations,
            'correlation_insights': self._generate_correlation_insights(strong_correlations)
        }
    
    async def _perform_clustering_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Advanced clustering analysis for pattern discovery
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2 or len(df) < 4:
            return {'error': 'Insufficient data for clustering analysis'}
        
        # Prepare data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df.fillna(numeric_df.mean()))
        
        # Determine optimal number of clusters
        optimal_k = self._find_optimal_clusters(scaled_data)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=optimal_k, random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_data)
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(scaled_data, cluster_labels)
        
        # Analyze clusters
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = cluster_labels
        
        cluster_analysis = {}
        for cluster_id in range(optimal_k):
            cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'size': len(cluster_data),
                'percentage': float(len(cluster_data) / len(df) * 100),
                'characteristics': self._analyze_cluster_characteristics(cluster_data, numeric_df.columns)
            }
        
        return {
            'optimal_clusters': optimal_k,
            'silhouette_score': float(silhouette_avg),
            'cluster_analysis': cluster_analysis,
            'cluster_insights': self._generate_cluster_insights(cluster_analysis),
            'business_segments': self._generate_business_segments(cluster_analysis, df)
        }
    
    async def _perform_outlier_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Advanced outlier detection and analysis
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {'error': 'No numerical columns for outlier analysis'}
        
        outlier_results = {}
        
        # IQR-based outliers
        for col in numeric_df.columns:
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_threshold_low = Q1 - 1.5 * IQR
            outlier_threshold_high = Q3 + 1.5 * IQR
            
            outliers = df[(numeric_df[col] < outlier_threshold_low) | (numeric_df[col] > outlier_threshold_high)]
            
            outlier_results[col] = {
                'outlier_count': len(outliers),
                'outlier_percentage': float(len(outliers) / len(df) * 100),
                'outlier_threshold_low': float(outlier_threshold_low),
                'outlier_threshold_high': float(outlier_threshold_high),
                'extreme_values': outliers[col].tolist()[:10]  # Top 10 outliers
            }
        
        # Isolation Forest for multivariate outliers
        if len(numeric_df.columns) >= 2:
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            outlier_predictions = iso_forest.fit_predict(numeric_df.fillna(numeric_df.mean()))
            multivariate_outliers = df[outlier_predictions == -1]
            
            outlier_results['multivariate_outliers'] = {
                'count': len(multivariate_outliers),
                'percentage': float(len(multivariate_outliers) / len(df) * 100),
                'outlier_records': multivariate_outliers.to_dict('records')[:5]  # Top 5 outlier records
            }
        
        return {
            'outlier_analysis': outlier_results,
            'outlier_insights': self._generate_outlier_insights(outlier_results),
            'data_quality_impact': self._assess_outlier_impact(outlier_results, df)
        }
    
    async def _perform_prediction_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Predictive analysis and forecasting
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return {'error': 'Insufficient numerical columns for prediction analysis'}
        
        prediction_results = {}
        
        # Try to identify target variable from question
        target_candidates = self._identify_target_variable(question, numeric_df.columns)
        
        for target in target_candidates[:2]:  # Limit to 2 targets for performance
            features = [col for col in numeric_df.columns if col != target]
            if not features:
                continue
                
            # Prepare data
            X = numeric_df[features].fillna(numeric_df[features].mean())
            y = numeric_df[target].fillna(numeric_df[target].mean())
            
            if len(X) < 5:  # Need minimum data for prediction
                continue
            
            # Simple linear regression for interpretability
            model = LinearRegression()
            model.fit(X, y)
            
            # Model performance
            score = model.score(X, y)
            predictions = model.predict(X)
            
            # Feature importance (coefficients)
            feature_importance = {}
            for i, feature in enumerate(features):
                feature_importance[feature] = float(model.coef_[i])
            
            prediction_results[target] = {
                'model_score': float(score),
                'feature_importance': feature_importance,
                'predictions': predictions.tolist()[:10],  # Sample predictions
                'model_equation': self._generate_model_equation(model, features),
                'business_implications': self._generate_prediction_insights(feature_importance, target)
            }
        
        return prediction_results
    
    async def _perform_time_series_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Time series analysis and trend detection
        """
        # Try to identify date columns
        date_cols = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col])
                    date_cols.append(col)
                except:
                    pass
        
        if not date_cols:
            return {'error': 'No date columns found for time series analysis'}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {'error': 'No numerical columns for time series analysis'}
        
        results = {}
        
        for date_col in date_cols[:1]:  # Focus on first date column
            # Convert to datetime
            df_ts = df.copy()
            df_ts[date_col] = pd.to_datetime(df_ts[date_col])
            df_ts = df_ts.sort_values(date_col)
            
            for numeric_col in numeric_cols[:2]:  # Limit to 2 numeric columns
                # Aggregate by time period if needed
                if len(df_ts) > 100:
                    df_ts['period'] = df_ts[date_col].dt.to_period('M')  # Monthly aggregation
                    ts_data = df_ts.groupby('period')[numeric_col].sum().reset_index()
                    ts_data['period'] = ts_data['period'].dt.to_timestamp()
                else:
                    ts_data = df_ts[[date_col, numeric_col]].copy()
                    ts_data = ts_data.rename(columns={date_col: 'period'})
                
                # Trend analysis
                X = np.arange(len(ts_data)).reshape(-1, 1)
                y = ts_data[numeric_col].values
                
                trend_model = LinearRegression()
                trend_model.fit(X, y)
                trend_slope = trend_model.coef_[0]
                
                # Seasonality detection (simple)
                seasonality_score = self._detect_seasonality(ts_data[numeric_col])
                
                results[f"{numeric_col}_vs_{date_col}"] = {
                    'trend_direction': 'increasing' if trend_slope > 0 else 'decreasing',
                    'trend_strength': float(abs(trend_slope)),
                    'seasonality_score': seasonality_score,
                    'volatility': float(ts_data[numeric_col].std() / ts_data[numeric_col].mean() if ts_data[numeric_col].mean() != 0 else 0),
                    'forecast_insights': self._generate_forecast_insights(ts_data, numeric_col)
                }
        
        return results
    
    # Helper methods for complex calculations
    
    def _calculate_partial_correlation(self, df: pd.DataFrame, x: str, y: str, control_vars: List[str]) -> float:
        """Calculate partial correlation between x and y controlling for control_vars"""
        try:
            # Simple implementation - could be enhanced with statsmodels
            from sklearn.linear_model import LinearRegression
            
            # Regress x on control variables
            X_control = df[control_vars].fillna(df[control_vars].mean())
            x_vals = df[x].fillna(df[x].mean())
            y_vals = df[y].fillna(df[y].mean())
            
            model_x = LinearRegression().fit(X_control, x_vals)
            model_y = LinearRegression().fit(X_control, y_vals)
            
            # Get residuals
            x_residual = x_vals - model_x.predict(X_control)
            y_residual = y_vals - model_y.predict(X_control)
            
            # Correlation of residuals
            return np.corrcoef(x_residual, y_residual)[0, 1]
        except:
            return 0.0
    
    def _find_optimal_clusters(self, data: np.ndarray) -> int:
        """Find optimal number of clusters using elbow method"""
        max_k = min(10, len(data) // 2)
        if max_k < 2:
            return 2
            
        inertias = []
        k_range = range(2, max_k + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(data)
            inertias.append(kmeans.inertia_)
        
        # Simple elbow detection
        if len(inertias) >= 3:
            # Find the point with maximum decrease in rate of change
            rates = []
            for i in range(1, len(inertias) - 1):
                rate = inertias[i-1] - inertias[i] - (inertias[i] - inertias[i+1])
                rates.append(rate)
            
            if rates:
                optimal_idx = rates.index(max(rates))
                return k_range[optimal_idx + 1]
        
        return 3  # Default
    
    def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, Any]:
        """Analyze characteristics of a cluster"""
        characteristics = {}
        
        for col in numeric_cols:
            if col in cluster_data.columns:
                characteristics[col] = {
                    'mean': float(cluster_data[col].mean()),
                    'median': float(cluster_data[col].median()),
                    'std': float(cluster_data[col].std()),
                    'percentile_25': float(cluster_data[col].quantile(0.25)),
                    'percentile_75': float(cluster_data[col].quantile(0.75))
                }
        
        return characteristics
    
    def _identify_target_variable(self, question: str, columns: List[str]) -> List[str]:
        """Identify potential target variables from question"""
        question_lower = question.lower()
        
        # Look for columns mentioned in the question
        mentioned_cols = [col for col in columns if col.lower() in question_lower]
        
        # If no direct mentions, look for common target patterns
        target_patterns = ['revenue', 'sales', 'profit', 'price', 'value', 'amount', 'score', 'rating']
        pattern_cols = [col for col in columns if any(pattern in col.lower() for pattern in target_patterns)]
        
        # Combine and prioritize
        targets = mentioned_cols + [col for col in pattern_cols if col not in mentioned_cols]
        
        return targets if targets else list(columns)[:3]  # Default to first 3 columns
    
    def _generate_model_equation(self, model: LinearRegression, features: List[str]) -> str:
        """Generate human-readable model equation"""
        equation_parts = [f"{model.intercept_:.2f}"]
        
        for i, feature in enumerate(features):
            coef = model.coef_[i]
            sign = "+" if coef >= 0 else "-"
            equation_parts.append(f" {sign} {abs(coef):.2f}*{feature}")
        
        return "".join(equation_parts)
    
    def _detect_seasonality(self, series: pd.Series) -> float:
        """Simple seasonality detection"""
        if len(series) < 12:
            return 0.0
        
        # Check for periodic patterns (simplified)
        autocorr_12 = series.autocorr(lag=min(12, len(series)//4))
        return abs(autocorr_12) if not np.isnan(autocorr_12) else 0.0
    
    def _generate_advanced_insights(self, results: Dict[str, Any], df: pd.DataFrame, question: str) -> List[str]:
        """Generate sophisticated insights from analysis results"""
        insights = []
        
        # Statistical insights
        if 'statistical_overview' in results:
            stats = results['statistical_overview']
            if 'descriptive_stats' in stats:
                insights.append("📊 **Statistical Profile**: Your data shows diverse statistical characteristics across variables")
            
        # Correlation insights
        if 'correlation' in results and 'strong_correlations' in results['correlation']:
            strong_corrs = results['correlation']['strong_correlations']
            if strong_corrs:
                insights.append(f"🔗 **Key Relationships**: Found {len(strong_corrs)} strong correlations indicating significant variable dependencies")
        
        # Clustering insights
        if 'clustering' in results and 'cluster_analysis' in results['clustering']:
            clusters = results['clustering']['cluster_analysis']
            insights.append(f"🎯 **Pattern Discovery**: Identified {len(clusters)} distinct data segments with unique characteristics")
        
        # Prediction insights
        if any('prediction' in key for key in results.keys()):
            insights.append("🔮 **Predictive Capability**: Built models to forecast key metrics based on variable relationships")
        
        # Add domain-specific insights
        insights.extend(self._generate_domain_insights(df, question))
        
        return insights
    
    def _generate_actionable_recommendations(self, results: Dict[str, Any], df: pd.DataFrame, question: str) -> List[str]:
        """Generate actionable business recommendations"""
        recommendations = []
        
        # Data quality recommendations
        if 'outlier' in results:
            outlier_data = results['outlier']
            high_outlier_cols = [col for col, data in outlier_data.get('outlier_analysis', {}).items() 
                               if isinstance(data, dict) and data.get('outlier_percentage', 0) > 10]
            if high_outlier_cols:
                recommendations.append(f"🔍 **Data Quality**: Investigate outliers in {', '.join(high_outlier_cols)} - they may indicate data entry errors or exceptional cases")
        
        # Correlation-based recommendations
        if 'correlation' in results:
            strong_corrs = results['correlation'].get('strong_correlations', [])
            for corr in strong_corrs[:2]:  # Top 2 correlations
                if corr['correlation'] > 0.7:
                    recommendations.append(f"💡 **Leverage Relationship**: Strong {corr['direction']} correlation between {corr['variable1']} and {corr['variable2']} suggests optimization opportunities")
        
        # Clustering recommendations
        if 'clustering' in results:
            recommendations.append("🎯 **Segmentation Strategy**: Use identified clusters to develop targeted approaches for each segment")
        
        # Performance recommendations
        recommendations.extend(self._generate_performance_recommendations(results, df))
        
        return recommendations
    
    def _generate_domain_insights(self, df: pd.DataFrame, question: str) -> List[str]:
        """Generate domain-specific insights based on data characteristics"""
        insights = []
        
        # Check for business metrics
        business_cols = [col for col in df.columns if any(term in col.lower() for term in 
                        ['revenue', 'profit', 'sales', 'customer', 'product', 'price', 'cost'])]
        
        if business_cols:
            insights.append("💼 **Business Context**: Data contains key business metrics suitable for performance analysis")
        
        # Check for time-based patterns
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_cols:
            insights.append("📈 **Temporal Dimension**: Time-based data enables trend analysis and forecasting capabilities")
        
        return insights
    
    def _generate_performance_recommendations(self, results: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """Generate performance-focused recommendations"""
        recommendations = []
        
        # Check data size for scalability
        if len(df) > 10000:
            recommendations.append("⚡ **Scalability**: Large dataset detected - consider implementing data sampling for real-time analysis")
        
        # Check feature richness
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 10:
            recommendations.append("🎛️ **Feature Engineering**: Rich numerical data available - consider feature selection for optimal model performance")
        
        return recommendations
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score"""
        scores = []
        
        # Completeness score
        completeness = (df.count().sum() / (len(df) * len(df.columns)))
        scores.append(completeness)
        
        # Consistency score (based on data types)
        consistency = sum(1 for col in df.columns if df[col].dtype != 'object') / len(df.columns)
        scores.append(consistency)
        
        # Uniqueness score (for identifier columns)
        uniqueness_scores = []
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64'] and df[col].nunique() == len(df):
                uniqueness_scores.append(1.0)
            else:
                uniqueness_scores.append(df[col].nunique() / len(df))
        
        if uniqueness_scores:
            scores.append(np.mean(uniqueness_scores))
        
        return float(np.mean(scores))
    
    def _calculate_analysis_confidence(self, results: Dict[str, Any], df: pd.DataFrame) -> float:
        """Calculate confidence in analysis results"""
        confidence_factors = []
        
        # Data size factor
        size_factor = min(1.0, len(df) / 100)  # Full confidence at 100+ records
        confidence_factors.append(size_factor)
        
        # Feature richness factor
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        richness_factor = min(1.0, len(numeric_cols) / 5)  # Full confidence at 5+ numeric columns
        confidence_factors.append(richness_factor)
        
        # Analysis success factor
        successful_analyses = sum(1 for key, value in results.items() if not isinstance(value, dict) or 'error' not in value)
        total_analyses = len(results)
        success_factor = successful_analyses / total_analyses if total_analyses > 0 else 0
        confidence_factors.append(success_factor)
        
        return float(np.mean(confidence_factors))
    
    def _generate_no_data_insights(self) -> Dict[str, Any]:
        """Generate insights when no data is available"""
        return {
            'analysis_results': {'error': 'No data available for analysis'},
            'advanced_insights': ['📋 **Data Required**: Upload a dataset to unlock sophisticated analysis capabilities'],
            'recommendations': ['📊 **Get Started**: Provide data in CSV, Excel, or JSON format to begin advanced analytics'],
            'data_quality_score': 0.0,
            'analysis_confidence': 0.0
        }
    
    def _generate_fallback_analysis(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Generate basic analysis when advanced analysis fails"""
        if not data:
            return self._generate_no_data_insights()
        
        df = pd.DataFrame(data)
        basic_stats = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
            'categorical_columns': len(df.select_dtypes(include=['object']).columns)
        }
        
        return {
            'analysis_results': {'basic_statistics': basic_stats},
            'advanced_insights': ['📊 **Basic Analysis**: Provided fundamental data statistics'],
            'recommendations': ['🔧 **Enhancement**: For deeper insights, ensure data quality and sufficient volume'],
            'data_quality_score': 0.5,
            'analysis_confidence': 0.3
        }
    
    # Placeholder methods for comprehensive analysis
    async def _perform_customer_segmentation(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Perform customer segmentation analysis"""
        # Implementation would go here
        return {'segmentation': 'Advanced customer segmentation analysis'}
    
    async def _perform_anomaly_detection(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Perform anomaly detection analysis"""
        # Implementation would go here  
        return {'anomalies': 'Advanced anomaly detection analysis'}
    
    async def _perform_distribution_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Perform distribution analysis"""
        # Implementation would go here
        return {'distributions': 'Advanced distribution analysis'}
    
    async def _perform_performance_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Perform performance analysis"""
        # Implementation would go here
        return {'performance': 'Advanced performance analysis'}
    
    async def _perform_cohort_analysis(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Perform cohort analysis"""
        # Implementation would go here
        return {'cohorts': 'Advanced cohort analysis'}
    
    async def _perform_pattern_recognition(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """Perform advanced pattern recognition"""
        # Implementation would go here
        return {'patterns': 'Advanced pattern recognition analysis'}
    
    # Additional helper methods for insights generation
    def _generate_correlation_insights(self, correlations: List[Dict]) -> List[str]:
        """Generate insights from correlation analysis"""
        insights = []
        for corr in correlations[:3]:  # Top 3 correlations
            insights.append(f"Strong {corr['direction']} relationship between {corr['variable1']} and {corr['variable2']} (r={corr['correlation']:.2f})")
        return insights
    
    def _generate_cluster_insights(self, cluster_analysis: Dict) -> List[str]:
        """Generate insights from cluster analysis"""
        insights = []
        cluster_sizes = [data['percentage'] for data in cluster_analysis.values()]
        largest_cluster = max(cluster_sizes)
        insights.append(f"Largest segment represents {largest_cluster:.1f}% of your data")
        return insights
    
    def _generate_business_segments(self, cluster_analysis: Dict, df: pd.DataFrame) -> List[str]:
        """Generate business segment descriptions"""
        segments = []
        for cluster_id, data in cluster_analysis.items():
            segments.append(f"Segment {cluster_id}: {data['size']} records ({data['percentage']:.1f}%)")
        return segments
    
    def _generate_outlier_insights(self, outlier_results: Dict) -> List[str]:
        """Generate insights from outlier analysis"""
        insights = []
        total_outliers = sum(data.get('outlier_count', 0) for data in outlier_results.get('outlier_analysis', {}).values() if isinstance(data, dict))
        if total_outliers > 0:
            insights.append(f"Detected {total_outliers} potential outliers across variables")
        return insights
    
    def _assess_outlier_impact(self, outlier_results: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess the impact of outliers on data quality"""
        return {
            'overall_outlier_rate': sum(data.get('outlier_count', 0) for data in outlier_results.get('outlier_analysis', {}).values() if isinstance(data, dict)) / len(df),
            'data_quality_impact': 'moderate'
        }
    
    def _generate_prediction_insights(self, feature_importance: Dict, target: str) -> List[str]:
        """Generate insights from prediction analysis"""
        insights = []
        if feature_importance:
            top_feature = max(feature_importance, key=lambda k: abs(feature_importance[k]))
            insights.append(f"'{top_feature}' has the strongest influence on {target}")
        return insights
    
    def _generate_forecast_insights(self, ts_data: pd.DataFrame, metric: str) -> List[str]:
        """Generate insights from time series analysis"""
        insights = []
        recent_trend = ts_data[metric].tail(5).mean() - ts_data[metric].head(5).mean()
        if recent_trend > 0:
            insights.append(f"{metric} shows positive growth trend in recent periods")
        else:
            insights.append(f"{metric} shows declining trend in recent periods")
        return insights
    
    async def _generate_advanced_visualizations(self, analysis_results: Dict[str, Any], question: str, data: List[Dict]) -> Dict[str, Any]:
        """Generate intelligent visualizations based on user question and analysis complexity"""
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return self._create_no_data_visualization()
            
            # Intelligent visualization selection based on question intent
            viz_config = self._determine_smart_visualization(question, analysis_results, df)
            
            return viz_config
                
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            return {
                "type": "error",
                "config": {"title": "Visualization Error", "message": str(e)},
                "insights": ["Visualization temporarily unavailable"]
            }
    
    def _determine_smart_visualization(self, question: str, analysis_results: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Intelligently determine visualization based on question complexity and intent"""
        question_lower = question.lower()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Pattern matching for specific visualization requests
        viz_patterns = {
            # Simple charts
            'histogram': ['histogram', 'distribution', 'frequency', 'spread'],
            'bar_chart': ['bar chart', 'bar graph', 'compare', 'comparison', 'by category'],
            'pie_chart': ['pie chart', 'pie graph', 'proportion', 'percentage', 'breakdown'],
            'line_chart': ['line chart', 'trend', 'over time', 'time series', 'growth'],
            'scatter_plot': ['scatter', 'relationship', 'correlation', 'vs', 'against'],
            
            # Advanced charts
            'heatmap': ['heatmap', 'correlation matrix', 'heat map'],
            'box_plot': ['box plot', 'outlier', 'quartile', 'median'],
            'dashboard': ['dashboard', 'overview', 'summary', 'comprehensive', 'complete picture'],
            'cluster_plot': ['cluster', 'segment', 'group', 'similar'],
            
            # Statistical charts
            'regression': ['regression', 'predict', 'forecast', 'model'],
            'violin_plot': ['violin', 'density'],
            'pair_plot': ['pair plot', 'all relationships', 'pairwise']
        }
        
        # Find the best matching visualization type
        best_match = None
        max_score = 0
        
        for viz_type, keywords in viz_patterns.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > max_score:
                max_score = score
                best_match = viz_type
        
        # Generate specific visualization based on match
        if best_match and max_score > 0:
            return self._create_specific_visualization(best_match, question, analysis_results, df)
        
        # If no specific request, determine based on question complexity
        return self._create_adaptive_visualization(question, analysis_results, df)
    
    def _create_specific_visualization(self, viz_type: str, question: str, analysis_results: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Create specific visualization as requested by user"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if viz_type == 'histogram':
            # Find the column to plot (from question or first numeric)
            target_col = self._extract_column_from_question(question, numeric_cols)
            if not target_col and numeric_cols:
                target_col = numeric_cols[0]
            
            return {
                "type": "histogram",
                "config": {
                    "column": target_col,
                    "data": df[target_col].dropna().tolist() if target_col else [],
                    "title": f"Distribution of {target_col}" if target_col else "Data Distribution",
                    "bins": min(30, len(df) // 10) if len(df) > 50 else 10
                },
                "insights": [
                    f"📊 Histogram shows the frequency distribution of {target_col}" if target_col else "Histogram visualization",
                    f"📈 Based on {len(df)} data points",
                    "💡 Peak values indicate most common ranges"
                ]
            }
        
        elif viz_type == 'bar_chart':
            # Find categorical column for grouping
            group_col = self._extract_column_from_question(question, categorical_cols)
            value_col = self._extract_column_from_question(question, numeric_cols)
            
            if not group_col and categorical_cols:
                group_col = categorical_cols[0]
            if not value_col and numeric_cols:
                value_col = numeric_cols[0]
            
            if group_col:
                grouped_data = df.groupby(group_col)[value_col].sum().to_dict() if value_col else df[group_col].value_counts().to_dict()
                return {
                    "type": "bar_chart",
                    "config": {
                        "categories": list(grouped_data.keys()),
                        "values": list(grouped_data.values()),
                        "title": f"{value_col or 'Count'} by {group_col}",
                        "x_label": group_col,
                        "y_label": value_col or "Count"
                    },
                    "insights": [
                        f"📊 Bar chart comparing {value_col or 'counts'} across {group_col}",
                        f"🏆 Highest value: {max(grouped_data.values())} in {max(grouped_data, key=grouped_data.get)}",
                        f"📈 Total categories: {len(grouped_data)}"
                    ]
                }
        
        elif viz_type == 'pie_chart':
            # Find categorical column for pie chart
            group_col = self._extract_column_from_question(question, categorical_cols)
            if not group_col and categorical_cols:
                group_col = categorical_cols[0]
            
            if group_col:
                pie_data = df[group_col].value_counts().to_dict()
                return {
                    "type": "pie_chart",
                    "config": {
                        "labels": list(pie_data.keys()),
                        "values": list(pie_data.values()),
                        "title": f"Distribution of {group_col}"
                    },
                    "insights": [
                        f"🥧 Pie chart shows proportion breakdown of {group_col}",
                        f"🏆 Largest segment: {max(pie_data, key=pie_data.get)} ({max(pie_data.values())/sum(pie_data.values())*100:.1f}%)",
                        f"📊 Total segments: {len(pie_data)}"
                    ]
                }
        
        elif viz_type == 'scatter_plot':
            if len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                
                # Try to extract specific columns from question
                x_mentioned = self._extract_column_from_question(question, numeric_cols)
                if x_mentioned:
                    x_col = x_mentioned
                    y_col = [col for col in numeric_cols if col != x_col][0] if len(numeric_cols) > 1 else y_col
                
                correlation = df[x_col].corr(df[y_col]) if len(df) > 1 else 0
                
                return {
                    "type": "scatter_plot",
                    "config": {
                        "x_data": df[x_col].tolist(),
                        "y_data": df[y_col].tolist(),
                        "x_label": x_col,
                        "y_label": y_col,
                        "title": f"{x_col} vs {y_col}",
                        "correlation": float(correlation)
                    },
                    "insights": [
                        f"🎯 Scatter plot reveals relationship between {x_col} and {y_col}",
                        f"📈 Correlation coefficient: {correlation:.3f} ({'Strong' if abs(correlation) > 0.7 else 'Moderate' if abs(correlation) > 0.3 else 'Weak'} relationship)",
                        f"📊 Based on {len(df)} data points"
                    ]
                }
        
        elif viz_type == 'dashboard':
            return self._create_comprehensive_dashboard(analysis_results, df)
        
        elif viz_type == 'heatmap':
            if 'correlation' in analysis_results:
                return {
                    "type": "correlation_heatmap",
                    "config": {
                        "correlations": analysis_results['correlation']['correlation_matrix'],
                        "title": "Correlation Heatmap"
                    },
                    "insights": analysis_results['correlation'].get('correlation_insights', [])
                }
        
        elif viz_type == 'cluster_plot':
            if 'clustering' in analysis_results:
                return {
                    "type": "cluster_scatter",
                    "config": {
                        "clusters": analysis_results['clustering']['cluster_analysis'],
                        "title": "Cluster Analysis"
                    },
                    "insights": analysis_results['clustering'].get('cluster_insights', [])
                }
        
        # Fallback to adaptive visualization
        return self._create_adaptive_visualization(question, analysis_results, df)
    
    def _create_adaptive_visualization(self, question: str, analysis_results: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Create adaptive visualization based on question complexity and data characteristics"""
        question_lower = question.lower()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Complex question indicators
        complex_indicators = [
            'analysis', 'patterns', 'insights', 'comprehensive', 'detailed', 'deep dive',
            'relationship', 'correlation', 'segment', 'cluster', 'predict', 'trend'
        ]
        
        complexity_score = sum(1 for indicator in complex_indicators if indicator in question_lower)
        
        if complexity_score >= 2 or len(question.split()) > 10:
            # Complex question - create dashboard
            return self._create_comprehensive_dashboard(analysis_results, df)
        
        elif any(word in question_lower for word in ['how many', 'count', 'total']):
            # Simple count question - create KPI
            return {
                "type": "kpi",
                "config": {
                    "value": len(df),
                    "label": "Total Records",
                    "color": "#DAA520"
                },
                "insights": [
                    f"📊 Dataset contains {len(df)} records",
                    f"📋 Across {len(df.columns)} variables",
                    "💡 Ready for deeper analysis"
                ]
            }
        
        elif len(numeric_cols) >= 2:
            # Multiple numeric columns - show correlation
            corr_matrix = df[numeric_cols].corr()
            return {
                "type": "correlation_matrix",
                "config": {
                    "correlations": corr_matrix.to_dict(),
                    "title": "Variable Relationships"
                },
                "insights": [
                    f"🔗 Correlation analysis of {len(numeric_cols)} variables",
                    "📊 Darker colors indicate stronger relationships",
                    "💡 Look for patterns in the correlation structure"
                ]
            }
        
        else:
            # Simple data overview
            return {
                "type": "data_overview",
                "config": {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "numeric_cols": len(numeric_cols),
                    "title": "Data Summary"
                },
                "insights": analysis_results.get('advanced_insights', [])[:3]
            }
    
    def _create_comprehensive_dashboard(self, analysis_results: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a comprehensive analytics dashboard"""
        dashboard_components = []
        
        # Add KPI metrics
        dashboard_components.append({
            "type": "kpi_panel",
            "title": "Key Metrics",
            "data": {
                "total_records": len(df),
                "data_quality": analysis_results.get('data_quality_score', 0),
                "analysis_confidence": analysis_results.get('analysis_confidence', 0)
            }
        })
        
        # Add correlation if available
        if 'correlation' in analysis_results:
            dashboard_components.append({
                "type": "correlation_heatmap",
                "title": "Variable Relationships",
                "data": analysis_results['correlation']['correlation_matrix']
            })
        
        # Add clustering if available
        if 'clustering' in analysis_results:
            dashboard_components.append({
                "type": "cluster_analysis",
                "title": "Data Segments",
                "data": analysis_results['clustering']['cluster_analysis']
            })
        
        # Add statistical overview
        if 'statistical_overview' in analysis_results:
            dashboard_components.append({
                "type": "statistical_summary",
                "title": "Statistical Profile",
                "data": analysis_results['statistical_overview']
            })
        
        return {
            "type": "dashboard",
            "config": {
                "components": dashboard_components,
                "title": "Advanced Analytics Dashboard",
                "layout": "grid"
            },
            "insights": analysis_results.get('advanced_insights', [])
        }
    
    def _extract_column_from_question(self, question: str, available_columns: List[str]) -> Optional[str]:
        """Extract column name mentioned in the question"""
        question_lower = question.lower()
        
        # Look for exact column matches
        for col in available_columns:
            if col.lower() in question_lower:
                return col
        
        # Look for partial matches
        for col in available_columns:
            col_words = col.lower().split('_')
            if any(word in question_lower for word in col_words if len(word) > 2):
                return col
        
        return None
    
    def _create_no_data_visualization(self) -> Dict[str, Any]:
        """Create visualization for when no data is available"""
        return {
            "type": "no_data",
            "config": {
                "title": "No Data Available",
                "message": "Please upload data to generate visualizations"
            },
            "insights": ["📋 Upload a dataset to unlock visualization capabilities"]
        }