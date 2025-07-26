"""
Enhanced Data ingestion and processing service
Handles files, databases, APIs, and HDFS with intelligent data understanding
"""

import pandas as pd
import numpy as np
import json
import os
import logging
import uuid
import asyncio
import chardet
# import xmltodict  # Optional XML support
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, create_engine
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import httpx
import aiofiles
from bs4 import BeautifulSoup

from app.database import DataSource, Dataset
from app.config import settings

logger = logging.getLogger(__name__)


class EnhancedDataIngestionService:
    """Enhanced service for processing multiple data sources"""
    
    def __init__(self):
        self.supported_formats = {
            # File formats
            'text/csv': self._process_csv,
            'application/vnd.ms-excel': self._process_excel,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': self._process_excel,
            'application/json': self._process_json,
            'application/parquet': self._process_parquet,
            'application/xml': self._process_xml,
            'text/xml': self._process_xml,
            'text/tsv': self._process_tsv,
            'text/tab-separated-values': self._process_tsv,
            
            # Database sources
            'database/postgresql': self._process_database,
            'database/mysql': self._process_database,
            'database/sqlite': self._process_database,
            
            # API sources
            'api/rest': self._process_api,
            'api/json': self._process_api,
            
            # HDFS
            'hdfs/parquet': self._process_hdfs,
            'hdfs/csv': self._process_hdfs
        }
    
    async def process_data_source(
        self, 
        source_config: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Universal data source processor
        
        Args:
            source_config: {
                'type': 'file|database|api|hdfs',
                'source': 'path|connection_string|url',
                'name': 'human readable name',
                'options': {} # additional options
            }
        """
        
        try:
            source_type = source_config.get('type')
            source_name = source_config.get('name', f'Data Source {uuid.uuid4().hex[:8]}')
            
            logger.info(f"Processing {source_type} data source: {source_name}")
            
            # Create data source record
            data_source = DataSource(
                name=source_name,
                original_filename=source_config.get('source', ''),
                file_type=source_type,
                file_size=0,  # Will be updated after processing
                processing_status="processing"
            )
            
            db.add(data_source)
            await db.commit()
            await db.refresh(data_source)
            
            # Process based on source type
            if source_type == 'file':
                df = await self._process_file_source(source_config)
            elif source_type == 'database':
                df = await self._process_database_source(source_config)
            elif source_type == 'api':
                df = await self._process_api_source(source_config)
            elif source_type == 'hdfs':
                df = await self._process_hdfs_source(source_config)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            # Enhanced data cleaning and preparation
            df_cleaned = await self._enhanced_clean_data(df)
            
            # Advanced schema generation
            schema_info = await self._generate_enhanced_schema(df_cleaned, source_config)
            
            # Create database table
            table_name = self._generate_table_name(source_name)
            await self._create_database_table(df_cleaned, table_name, db)
            
            # Update data source
            data_source.processing_status = "completed"
            data_source.row_count = len(df_cleaned)
            data_source.column_count = len(df_cleaned.columns)
            data_source.file_size = df_cleaned.memory_usage(deep=True).sum()
            data_source.schema_info = schema_info
            
            # Create dataset record
            dataset = Dataset(
                data_source_id=data_source.id,
                table_name=table_name,
                display_name=source_name,
                description=f"Processed data from {source_type} source",
                schema_definition=schema_info,
                sample_questions=await self._generate_intelligent_questions(schema_info, source_name, df_cleaned)
            )
            
            db.add(dataset)
            await db.commit()
            
            logger.info(f"Successfully processed {source_name}: {len(df_cleaned)} rows, {len(df_cleaned.columns)} columns")
            
            return {
                "success": True,
                "data_source_id": str(data_source.id),
                "dataset_id": str(dataset.id),
                "table_name": table_name,
                "row_count": len(df_cleaned),
                "column_count": len(df_cleaned.columns),
                "schema": schema_info,
                "sample_questions": dataset.sample_questions
            }
            
        except Exception as e:
            logger.error(f"Processing failed for {source_name}: {e}")
            if 'data_source' in locals():
                data_source.processing_status = "failed"
                await db.commit()
            raise
    
    async def _process_file_source(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Process file-based data sources"""
        
        file_path = config['source']
        options = config.get('options', {})
        
        # Auto-detect file format if not specified
        if 'format' not in options:
            format_type = await self._detect_file_format(file_path)
        else:
            format_type = options['format']
        
        processor = self.supported_formats.get(format_type)
        if not processor:
            raise ValueError(f"Unsupported file format: {format_type}")
        
        return await processor(file_path, options)
    
    async def _process_database_source(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Process database sources"""
        
        connection_string = config['source']
        options = config.get('options', {})
        
        # Parse connection details
        parsed = urlparse(connection_string)
        db_type = parsed.scheme
        
        # Build query
        table_name = options.get('table')
        query = options.get('query')
        
        if not table_name and not query:
            raise ValueError("Either 'table' or 'query' must be specified for database sources")
        
        if not query:
            query = f"SELECT * FROM {table_name}"
            if 'limit' in options:
                query += f" LIMIT {options['limit']}"
        
        # Create connection and fetch data
        engine = create_engine(connection_string)
        
        try:
            df = pd.read_sql(query, engine)
            logger.info(f"Loaded {len(df)} rows from database")
            return df
        finally:
            engine.dispose()
    
    async def _process_api_source(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Process REST API sources"""
        
        url = config['source']
        options = config.get('options', {})
        
        headers = options.get('headers', {})
        params = options.get('params', {})
        auth = options.get('auth')
        timeout = options.get('timeout', 30)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if auth:
                if auth.get('type') == 'bearer':
                    headers['Authorization'] = f"Bearer {auth['token']}"
                elif auth.get('type') == 'basic':
                    client.auth = (auth['username'], auth['password'])
            
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'json' in content_type:
                data = response.json()
                df = pd.json_normalize(data)
            elif 'csv' in content_type:
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
            elif 'xml' in content_type:
                data = xmltodict.parse(response.text)
                df = pd.json_normalize(data)
            else:
                # Try to parse as JSON by default
                try:
                    data = response.json()
                    df = pd.json_normalize(data)
                except:
                    raise ValueError(f"Unsupported API response format: {content_type}")
        
        logger.info(f"Loaded {len(df)} rows from API")
        return df
    
    async def _process_hdfs_source(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Process HDFS sources (simplified for local deployment)"""
        
        # For local deployment, treat HDFS paths as local file paths
        # In production, this would use hdfs3 or similar
        hdfs_path = config['source']
        options = config.get('options', {})
        
        if hdfs_path.startswith('hdfs://'):
            # Remove hdfs:// prefix for local processing
            local_path = hdfs_path.replace('hdfs://', '/hdfs/')
        else:
            local_path = hdfs_path
        
        if local_path.endswith('.parquet'):
            df = pd.read_parquet(local_path)
        elif local_path.endswith('.csv'):
            df = pd.read_csv(local_path)
        else:
            raise ValueError(f"Unsupported HDFS file format: {local_path}")
        
        logger.info(f"Loaded {len(df)} rows from HDFS")
        return df
    
    async def _detect_file_format(self, file_path: str) -> str:
        """Auto-detect file format based on extension and content"""
        
        # Get file extension
        _, ext = os.path.splitext(file_path.lower())
        
        # Map extensions to MIME types
        ext_mapping = {
            '.csv': 'text/csv',
            '.tsv': 'text/tsv',
            '.txt': 'text/csv',  # Assume CSV by default
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.json': 'application/json',
            '.parquet': 'application/parquet',
            '.xml': 'application/xml',
        }
        
        detected_format = ext_mapping.get(ext)
        
        if not detected_format:
            # Try to detect from content
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read(1024)  # Read first 1KB
                    
                # Detect encoding
                encoding_result = chardet.detect(content)
                encoding = encoding_result.get('encoding', 'utf-8')
                
                # Decode and check content
                text_content = content.decode(encoding, errors='ignore')
                
                if text_content.strip().startswith(('<?xml', '<')):
                    detected_format = 'application/xml'
                elif text_content.strip().startswith(('{', '[')):
                    detected_format = 'application/json'
                else:
                    detected_format = 'text/csv'  # Default fallback
            except:
                detected_format = 'text/csv'  # Final fallback
        
        logger.info(f"Detected format for {file_path}: {detected_format}")
        return detected_format
    
    async def _process_csv(self, file_path: str, options: Dict[str, Any] = None) -> pd.DataFrame:
        """Enhanced CSV processing with better detection"""
        
        options = options or {}
        
        # Detect encoding
        async with aiofiles.open(file_path, 'rb') as f:
            raw_content = await f.read()
            encoding_result = chardet.detect(raw_content)
            encoding = encoding_result.get('encoding', 'utf-8')
        
        # Try different delimiters and parameters
        delimiters = options.get('delimiters', [',', ';', '\t', '|'])
        
        best_df = None
        max_columns = 0
        
        for delimiter in delimiters:
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter=delimiter,
                    encoding=encoding,
                    low_memory=False,
                    skipinitialspace=True,
                    na_values=['', 'NULL', 'null', 'N/A', 'n/a', '#N/A']
                )
                
                if len(df.columns) > max_columns and len(df) > 0:
                    max_columns = len(df.columns)
                    best_df = df
                    
            except Exception as e:
                logger.debug(f"Failed to parse with delimiter '{delimiter}': {e}")
                continue
        
        if best_df is None:
            raise ValueError("Could not parse CSV file with any delimiter")
        
        logger.info(f"CSV loaded with {len(best_df)} rows and {len(best_df.columns)} columns")
        return best_df
    
    async def _process_tsv(self, file_path: str, options: Dict[str, Any] = None) -> pd.DataFrame:
        """Process TSV (Tab-separated values) files"""
        options = options or {}
        options['delimiters'] = ['\t']
        return await self._process_csv(file_path, options)
    
    async def _process_xml(self, file_path: str, options: Dict[str, Any] = None) -> pd.DataFrame:
        """Process XML files"""
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                xml_content = await f.read()
            
            # Parse XML to dictionary
            data_dict = xmltodict.parse(xml_content)
            
            # Find the main data array in the XML structure
            df = self._extract_dataframe_from_xml(data_dict)
            
            logger.info(f"XML loaded with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"XML processing failed: {e}")
            raise ValueError(f"Could not parse XML file: {e}")
    
    def _extract_dataframe_from_xml(self, data_dict: Dict) -> pd.DataFrame:
        """Extract DataFrame from XML dictionary structure"""
        
        # Try to find arrays/lists in the XML structure
        def find_arrays(obj, path=""):
            arrays = []
            if isinstance(obj, list) and len(obj) > 0:
                arrays.append((path, obj))
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    arrays.extend(find_arrays(value, new_path))
            return arrays
        
        arrays = find_arrays(data_dict)
        
        if not arrays:
            # No arrays found, convert the whole structure
            return pd.json_normalize([data_dict])
        
        # Use the largest array found
        largest_array = max(arrays, key=lambda x: len(x[1]))
        return pd.json_normalize(largest_array[1])
    
    async def _enhanced_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced data cleaning with intelligent type detection"""
        
        logger.info("Starting enhanced data cleaning...")
        
        df_clean = df.copy()
        
        # Remove completely empty rows and columns
        df_clean = df_clean.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names more intelligently
        df_clean.columns = [
            self._clean_column_name(col) for col in df_clean.columns
        ]
        
        # Handle duplicate column names
        df_clean = self._handle_duplicate_columns(df_clean)
        
        # Advanced data type inference
        df_clean = await self._enhanced_type_inference(df_clean)
        
        # Remove duplicates
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        duplicates_removed = initial_rows - len(df_clean)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        # Data quality assessment
        quality_report = self._assess_data_quality(df_clean)
        logger.info(f"Data quality score: {quality_report['overall_score']:.2f}")
        
        logger.info(f"Enhanced cleaning completed. Final shape: {df_clean.shape}")
        
        return df_clean
    
    def _clean_column_name(self, col: str) -> str:
        """Clean column names more intelligently"""
        
        # Convert to string if not already
        col = str(col)
        
        # Remove common prefixes/suffixes
        col = col.strip()
        
        # Handle camelCase and PascalCase
        import re
        col = re.sub('([a-z0-9])([A-Z])', r'\1_\2', col)
        
        # Replace spaces and special characters
        col = re.sub(r'[^\w\s]', '_', col)
        col = re.sub(r'\s+', '_', col)
        
        # Convert to lowercase
        col = col.lower()
        
        # Remove multiple underscores
        col = re.sub(r'_+', '_', col)
        
        # Remove leading/trailing underscores
        col = col.strip('_')
        
        # Ensure it doesn't start with a number
        if col and col[0].isdigit():
            col = f'col_{col}'
        
        # Handle empty names
        if not col:
            col = f'unnamed_column_{uuid.uuid4().hex[:8]}'
        
        return col
    
    def _handle_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle duplicate column names intelligently"""
        
        cols = list(df.columns)
        seen = {}
        
        for i, col in enumerate(cols):
            if col in seen:
                seen[col] += 1
                cols[i] = f"{col}_{seen[col]}"
            else:
                seen[col] = 0
        
        df.columns = cols
        return df
    
    async def _enhanced_type_inference(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced data type inference with business logic"""
        
        for col in df.columns:
            series = df[col]
            
            # Skip if already properly typed
            if series.dtype in ['int64', 'float64', 'datetime64[ns]', 'bool']:
                continue
            
            # Try numeric conversion first
            if series.dtype == 'object':
                # Check for currency values
                if self._looks_like_currency(series):
                    df[col] = self._parse_currency(series)
                    continue
                
                # Check for percentages
                elif self._looks_like_percentage(series):
                    df[col] = self._parse_percentage(series)
                    continue
                
                # Check for dates
                elif self._looks_like_date(series):
                    df[col] = pd.to_datetime(series, errors='coerce', infer_datetime_format=True)
                    continue
                
                # Check for boolean values
                elif self._looks_like_boolean(series):
                    df[col] = self._parse_boolean(series)
                    continue
                
                # Try numeric conversion
                numeric_series = pd.to_numeric(series, errors='coerce')
                if not numeric_series.isna().all():
                    # Check if integers or floats
                    if numeric_series.dropna().apply(lambda x: x.is_integer()).all():
                        df[col] = numeric_series.astype('Int64')  # Nullable integer
                    else:
                        df[col] = numeric_series
                    continue
        
        return df
    
    def _looks_like_currency(self, series: pd.Series) -> bool:
        """Check if series looks like currency values"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        currency_pattern = r'^[\$£€¥]?[\d,]+\.?\d*$'
        import re
        matches = sample.str.match(currency_pattern, na=False).sum()
        return matches > len(sample) * 0.7
    
    def _parse_currency(self, series: pd.Series) -> pd.Series:
        """Parse currency values to numeric"""
        import re
        return series.astype(str).str.replace(r'[\$£€¥,]', '', regex=True).astype(float)
    
    def _looks_like_percentage(self, series: pd.Series) -> bool:
        """Check if series looks like percentage values"""
        sample = series.dropna().astype(str).head(10)
        if len(sample) == 0:
            return False
        
        percentage_pattern = r'^\d+\.?\d*%$'
        import re
        matches = sample.str.match(percentage_pattern, na=False).sum()
        return matches > len(sample) * 0.7
    
    def _parse_percentage(self, series: pd.Series) -> pd.Series:
        """Parse percentage values to numeric (0-1 scale)"""
        return series.astype(str).str.replace('%', '').astype(float) / 100
    
    def _looks_like_date(self, series: pd.Series) -> bool:
        """Check if series looks like date values"""
        sample = series.dropna().head(10)
        if len(sample) == 0:
            return False
        
        try:
            parsed = pd.to_datetime(sample, errors='coerce')
            valid_dates = parsed.notna().sum()
            return valid_dates > len(sample) * 0.7
        except:
            return False
    
    def _looks_like_boolean(self, series: pd.Series) -> bool:
        """Check if series looks like boolean values"""
        unique_values = set(series.dropna().astype(str).str.lower().unique())
        boolean_values = {'true', 'false', 'yes', 'no', '1', '0', 'y', 'n', 'on', 'off'}
        return unique_values.issubset(boolean_values) and len(unique_values) <= 6
    
    def _parse_boolean(self, series: pd.Series) -> pd.Series:
        """Parse boolean-like values"""
        mapping = {
            'true': True, 'false': False,
            'yes': True, 'no': False,
            'y': True, 'n': False,
            '1': True, '0': False,
            'on': True, 'off': False
        }
        
        return series.astype(str).str.lower().map(mapping)
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality and return metrics"""
        
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        
        quality_metrics = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_percentage': (missing_cells / total_cells) * 100 if total_cells > 0 else 0,
            'duplicate_rows': len(df) - len(df.drop_duplicates()),
            'overall_score': max(0, 100 - (missing_cells / total_cells) * 100) if total_cells > 0 else 0
        }
        
        return quality_metrics
    
    async def _generate_enhanced_schema(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced schema with business intelligence"""
        
        schema = {}
        
        for col in df.columns:
            col_info = {
                "type": self._infer_business_type(df[col]),
                "description": self._generate_smart_description(col, df[col]),
                "nullable": df[col].isna().any(),
                "unique_values": min(df[col].nunique(), 20),
                "missing_percentage": (df[col].isna().sum() / len(df)) * 100,
                "data_quality_score": self._calculate_column_quality(df[col])
            }
            
            # Add type-specific metadata
            if col_info["type"] in ["number", "currency", "percentage"]:
                col_info.update(self._get_numeric_stats(df[col]))
            elif col_info["type"] == "category":
                col_info.update(self._get_categorical_stats(df[col]))
            elif col_info["type"] == "date":
                col_info.update(self._get_date_stats(df[col]))
            
            schema[col] = col_info
        
        return schema
    
    def _infer_business_type(self, series: pd.Series) -> str:
        """Infer business-relevant data types"""
        
        if pd.api.types.is_numeric_dtype(series):
            # Check for specific numeric subtypes
            col_name = series.name.lower() if series.name else ""
            
            if any(term in col_name for term in ['price', 'cost', 'amount', 'revenue', 'salary']):
                return "currency"
            elif any(term in col_name for term in ['rate', 'percent', 'ratio']):
                return "percentage"
            elif any(term in col_name for term in ['id', 'count', 'quantity', 'number']):
                return "identifier" if 'id' in col_name else "number"
            else:
                return "number"
                
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "date"
            
        elif pd.api.types.is_bool_dtype(series):
            return "boolean"
            
        else:
            # String/object type - determine if categorical
            unique_ratio = series.nunique() / len(series) if len(series) > 0 else 0
            
            if unique_ratio < 0.1 and series.nunique() < 50:
                return "category"
            elif any(term in series.name.lower() for term in ['email', 'mail']):
                return "email"
            elif any(term in series.name.lower() for term in ['url', 'link']):
                return "url"
            elif any(term in series.name.lower() for term in ['phone', 'mobile']):
                return "phone"
            else:
                return "text"
    
    def _generate_smart_description(self, col_name: str, series: pd.Series) -> str:
        """Generate intelligent column descriptions"""
        
        col_lower = col_name.lower()
        data_type = self._infer_business_type(series)
        
        # Pattern-based descriptions
        patterns = {
            'customer': 'Customer information',
            'user': 'User data',
            'product': 'Product details',
            'order': 'Order information',
            'transaction': 'Transaction record',
            'payment': 'Payment details',
            'address': 'Address information',
            'date': 'Date/time information',
            'created': 'Creation timestamp',
            'updated': 'Last update timestamp',
            'status': 'Status indicator',
            'category': 'Category classification',
            'type': 'Type classification',
            'name': 'Name or title',
            'email': 'Email address',
            'phone': 'Phone number',
            'amount': 'Monetary amount',
            'price': 'Price value',
            'cost': 'Cost amount',
            'revenue': 'Revenue figure',
            'count': 'Count or quantity',
            'id': 'Unique identifier',
            'description': 'Descriptive text'
        }
        
        for pattern, description in patterns.items():
            if pattern in col_lower:
                return description
        
        # Fallback to type-based description
        type_descriptions = {
            'currency': 'Monetary value',
            'percentage': 'Percentage value',
            'number': 'Numeric value',
            'date': 'Date/time value',
            'category': 'Categorical data',
            'boolean': 'Yes/no indicator',
            'email': 'Email address',
            'phone': 'Phone number',
            'url': 'Web address',
            'identifier': 'Unique identifier',
            'text': 'Text data'
        }
        
        return type_descriptions.get(data_type, f"Data column: {col_name.replace('_', ' ').title()}")
    
    def _calculate_column_quality(self, series: pd.Series) -> float:
        """Calculate data quality score for a column"""
        
        if len(series) == 0:
            return 0.0
            
        # Factors affecting quality
        completeness = (len(series) - series.isna().sum()) / len(series)
        uniqueness = series.nunique() / len(series) if len(series) > 0 else 0
        
        # Penalize very low uniqueness (except for legitimate categories)
        if uniqueness < 0.01 and series.nunique() > 1:
            uniqueness_penalty = 0.1
        else:
            uniqueness_penalty = 0
        
        quality_score = (completeness * 0.7 + uniqueness * 0.3 - uniqueness_penalty) * 100
        return max(0, min(100, quality_score))
    
    def _get_numeric_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for numeric columns"""
        
        clean_series = series.dropna()
        if len(clean_series) == 0:
            return {}
        
        return {
            "min": float(clean_series.min()),
            "max": float(clean_series.max()),
            "mean": float(clean_series.mean()),
            "median": float(clean_series.median()),
            "std": float(clean_series.std()) if len(clean_series) > 1 else 0,
            "has_outliers": self._detect_outliers(clean_series)
        }
    
    def _get_categorical_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for categorical columns"""
        
        value_counts = series.value_counts()
        
        return {
            "top_values": value_counts.head(10).to_dict(),
            "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else None,
            "category_count": len(value_counts)
        }
    
    def _get_date_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Get statistics for date columns"""
        
        clean_series = series.dropna()
        if len(clean_series) == 0:
            return {}
        
        return {
            "min_date": clean_series.min().isoformat() if hasattr(clean_series.min(), 'isoformat') else str(clean_series.min()),
            "max_date": clean_series.max().isoformat() if hasattr(clean_series.max(), 'isoformat') else str(clean_series.max()),
            "date_range_days": (clean_series.max() - clean_series.min()).days if hasattr(clean_series.max() - clean_series.min(), 'days') else 0
        }
    
    def _detect_outliers(self, series: pd.Series) -> bool:
        """Detect if numeric series has outliers using IQR method"""
        
        if len(series) < 4:
            return False
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return len(outliers) > 0
    
    async def _generate_intelligent_questions(self, schema: Dict[str, Any], dataset_name: str, df: pd.DataFrame) -> List[str]:
        """Generate intelligent sample questions based on data analysis"""
        
        questions = []
        
        # Analyze the data to generate contextual questions
        numeric_cols = [col for col, info in schema.items() if info['type'] in ['number', 'currency', 'percentage']]
        categorical_cols = [col for col, info in schema.items() if info['type'] == 'category']
        date_cols = [col for col, info in schema.items() if info['type'] == 'date']
        
        # Basic questions
        questions.extend([
            f"How many records are in {dataset_name}?",
            f"Show me a summary of {dataset_name}",
            f"What are the main characteristics of this data?"
        ])
        
        # Numeric analysis questions
        for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            col_display = col.replace('_', ' ').title()
            questions.extend([
                f"What is the average {col_display}?",
                f"Show me the distribution of {col_display}",
                f"What are the highest and lowest {col_display} values?"
            ])
        
        # Categorical analysis questions
        for col in categorical_cols[:2]:  # Limit to first 2 categorical columns
            col_display = col.replace('_', ' ').title()
            questions.extend([
                f"How many records by {col_display}?",
                f"Show me the breakdown of {col_display}",
                f"What is the most common {col_display}?"
            ])
        
        # Time-based questions if date columns exist
        if date_cols:
            date_col = date_cols[0]
            date_display = date_col.replace('_', ' ').title()
            questions.extend([
                f"Show me trends over time",
                f"What was the activity by month?",
                f"How has the data changed over time?"
            ])
        
        # Cross-analysis questions
        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            num_col = numeric_cols[0].replace('_', ' ').title()
            cat_col = categorical_cols[0].replace('_', ' ').title()
            questions.append(f"Compare {num_col} across different {cat_col}")
        
        # Business intelligence questions based on common patterns
        col_names = [col.lower() for col in schema.keys()]
        
        if any('customer' in col for col in col_names):
            questions.append("Which customers are most valuable?")
        
        if any('product' in col for col in col_names):
            questions.append("What are the top-performing products?")
        
        if any('sales' in col or 'revenue' in col for col in col_names):
            questions.append("What are our sales trends?")
        
        if any('status' in col for col in col_names):
            questions.append("What is the status distribution?")
        
        # Limit total questions
        return questions[:12]
    
    def _generate_table_name(self, base_name: str) -> str:
        """Generate a safe table name"""
        
        # Clean the name
        table_name = base_name.lower().replace(' ', '_').replace('-', '_')
        table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')
        
        # Add prefix to avoid conflicts
        table_name = f"data_{table_name}_{str(uuid.uuid4())[:8]}"
        
        return table_name
    
    async def _create_database_table(
        self, 
        df: pd.DataFrame, 
        table_name: str, 
        db: AsyncSession
    ):
        """Create database table and insert data with better type mapping"""
        
        logger.info(f"Creating table: {table_name}")
        
        # Generate CREATE TABLE statement with improved type mapping
        columns = []
        for col in df.columns:
            sql_type = self._get_enhanced_sql_type(df[col])
            columns.append(f'"{col}" {sql_type}')
        
        create_sql = f"""
        CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            {', '.join(columns)}
        )
        """
        
        # Create table
        await db.execute(text(create_sql))
        
        # Insert data in batches with better error handling
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]
            
            # Clean batch data for insertion
            batch_clean = batch.copy()
            for col in batch_clean.columns:
                # Handle NaN values
                if batch_clean[col].dtype == 'object':
                    batch_clean[col] = batch_clean[col].fillna('')
                else:
                    batch_clean[col] = batch_clean[col].fillna(0)
                
                # Convert datetime to string for JSON serialization
                if pd.api.types.is_datetime64_any_dtype(batch_clean[col]):
                    batch_clean[col] = batch_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare insert statement
            placeholders = ', '.join([f':{col}' for col in df.columns])
            quoted_columns = ', '.join([f'"{col}"' for col in df.columns])
            insert_sql = f"INSERT INTO {table_name} ({quoted_columns}) VALUES ({placeholders})"
            
            # Convert batch to records
            records = batch_clean.to_dict('records')
            
            try:
                # Execute batch insert
                await db.execute(text(insert_sql), records)
                total_inserted += len(records)
            except Exception as e:
                logger.error(f"Failed to insert batch {i//batch_size + 1}: {e}")
                # Try to insert records one by one
                for record in records:
                    try:
                        await db.execute(text(insert_sql), record)
                        total_inserted += 1
                    except Exception as record_error:
                        logger.warning(f"Failed to insert record: {record_error}")
        
        await db.commit()
        logger.info(f"Inserted {total_inserted} rows into {table_name}")
    
    def _get_enhanced_sql_type(self, series: pd.Series) -> str:
        """Enhanced SQL type mapping"""
        
        if pd.api.types.is_integer_dtype(series):
            return "INTEGER"
        elif pd.api.types.is_float_dtype(series):
            return "DECIMAL(15,4)"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "TIMESTAMP"
        elif pd.api.types.is_bool_dtype(series):
            return "BOOLEAN"
        else:
            # Determine appropriate text type based on content
            max_length = series.astype(str).str.len().max() if len(series) > 0 else 0
            
            if max_length <= 50:
                return "VARCHAR(255)"
            elif max_length <= 1000:
                return "VARCHAR(2000)"
            else:
                return "TEXT"