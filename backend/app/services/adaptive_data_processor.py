"""
Adaptive Data Processing Engine
Automatically adapts to any data format, schema, and business context
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, date
import re
from pathlib import Path
import chardet
import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.database import DataSource, Dataset, get_db
from app.services.enhanced_llm_service import EnhancedLLMService

logger = logging.getLogger(__name__)


class AdaptiveDataProcessor:
    """
    Intelligent data processor that adapts to any data format and business context
    """
    
    def __init__(self):
        self.llm_service = EnhancedLLMService()
        self.supported_formats = {
            'csv': self._process_csv,
            'xlsx': self._process_excel,
            'xls': self._process_excel,
            'json': self._process_json,
            'xml': self._process_xml,
            'tsv': self._process_tsv,
            'parquet': self._process_parquet,
            'txt': self._process_text
        }
    
    async def process_any_data(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """
        Intelligently process any data format and adapt to its structure
        """
        try:
            # 1. Auto-detect file format and encoding
            file_info = await self._detect_file_format(file_path, original_filename)
            
            # 2. Load and parse data based on detected format
            raw_data = await self._load_data(file_path, file_info)
            
            # 3. Intelligent data profiling and understanding
            data_profile = await self._profile_data_intelligently(raw_data, original_filename)
            
            # 4. Adaptive data cleaning and standardization
            clean_data = await self._adaptive_data_cleaning(raw_data, data_profile)
            
            # 5. Generate business-friendly schema
            business_schema = await self._generate_business_schema(clean_data, data_profile)
            
            # 6. Create adaptive sample questions
            sample_questions = await self._generate_adaptive_questions(clean_data, business_schema, data_profile)
            
            # 7. Store processed data with dynamic table structure
            table_name = await self._store_adaptive_data(clean_data, business_schema, original_filename)
            
            return {
                'success': True,
                'table_name': table_name,
                'schema': business_schema,
                'profile': data_profile,
                'sample_questions': sample_questions,
                'row_count': len(clean_data),
                'column_count': len(clean_data.columns) if hasattr(clean_data, 'columns') else 0
            }
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _detect_file_format(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Intelligently detect file format, encoding, and structure
        """
        # Get file extension
        extension = Path(filename).suffix.lower().lstrip('.')
        
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result.get('encoding', 'utf-8')
        
        # Advanced format detection for ambiguous cases
        if extension in ['txt', 'dat', '']:
            # Try to detect if it's CSV, TSV, or other format
            with open(file_path, 'r', encoding=encoding) as f:
                first_lines = [f.readline().strip() for _ in range(5)]
                
            # Check for delimiters
            if any(',' in line for line in first_lines):
                extension = 'csv'
            elif any('\t' in line for line in first_lines):
                extension = 'tsv'
            elif first_lines[0].startswith('{') or first_lines[0].startswith('['):
                extension = 'json'
            elif first_lines[0].startswith('<'):
                extension = 'xml'
        
        return {
            'format': extension,
            'encoding': encoding,
            'confidence': encoding_result.get('confidence', 0.9)
        }
    
    async def _load_data(self, file_path: str, file_info: Dict[str, Any]) -> pd.DataFrame:
        """
        Load data using the appropriate method based on detected format
        """
        format_type = file_info['format']
        encoding = file_info['encoding']
        
        if format_type in self.supported_formats:
            return await self.supported_formats[format_type](file_path, encoding)
        else:
            # Fallback to CSV with intelligent delimiter detection
            return await self._process_csv(file_path, encoding)
    
    async def _process_csv(self, file_path: str, encoding: str) -> pd.DataFrame:
        """Smart CSV processing with delimiter detection"""
        # Try different delimiters
        delimiters = [',', ';', '\t', '|', ':']
        
        for delimiter in delimiters:
            try:
                df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, 
                               nrows=5, skipinitialspace=True)
                if len(df.columns) > 1:  # Found the right delimiter
                    # Load full file
                    df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter,
                                   skipinitialspace=True)
                    return df
            except:
                continue
        
        # Fallback to default comma delimiter
        return pd.read_csv(file_path, encoding=encoding)
    
    async def _process_excel(self, file_path: str, encoding: str) -> pd.DataFrame:
        """Smart Excel processing with sheet detection"""
        excel_file = pd.ExcelFile(file_path)
        
        # If multiple sheets, try to find the main data sheet
        if len(excel_file.sheet_names) == 1:
            return pd.read_excel(file_path, sheet_name=0)
        
        # Find sheet with most data
        best_sheet = None
        max_rows = 0
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
                if len(df) > max_rows:
                    max_rows = len(df)
                    best_sheet = sheet_name
            except:
                continue
        
        return pd.read_excel(file_path, sheet_name=best_sheet or 0)
    
    async def _process_json(self, file_path: str, encoding: str) -> pd.DataFrame:
        """Smart JSON processing with nested structure handling"""
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            return pd.json_normalize(data)
        elif isinstance(data, dict):
            # Find the main data array
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    return pd.json_normalize(value)
            # If no list found, normalize the dict
            return pd.json_normalize([data])
        
        return pd.DataFrame([data])
    
    async def _process_xml(self, file_path: str, encoding: str) -> pd.DataFrame:
        """Smart XML processing"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Find repeating elements (likely data rows)
        element_counts = {}
        for child in root:
            tag = child.tag
            element_counts[tag] = element_counts.get(tag, 0) + 1
        
        # Find the most common element (likely data rows)
        if element_counts:
            data_element = max(element_counts, key=element_counts.get)
            
            # Extract data from these elements
            data = []
            for elem in root.findall(data_element):
                row = {}
                for child in elem:
                    row[child.tag] = child.text
                data.append(row)
            
            return pd.DataFrame(data)
        
        # Fallback: convert entire XML to flat structure
        return pd.json_normalize([ET.parse(file_path).getroot().attrib])
    
    async def _process_tsv(self, file_path: str, encoding: str) -> pd.DataFrame:
        """TSV processing"""
        return pd.read_csv(file_path, encoding=encoding, delimiter='\t')
    
    async def _process_parquet(self, file_path: str, encoding: str) -> pd.DataFrame:
        """Parquet processing"""
        return pd.read_parquet(file_path)
    
    async def _process_text(self, file_path: str, encoding: str) -> pd.DataFrame:
        """Process plain text files by trying to detect structure"""
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        # Try to detect if it's structured data
        if len(lines) > 1:
            # Check for common patterns
            first_line = lines[0].strip()
            if ',' in first_line:
                return await self._process_csv(file_path, encoding)
            elif '\t' in first_line:
                return await self._process_tsv(file_path, encoding)
        
        # Treat as single column text data
        return pd.DataFrame({'text': [line.strip() for line in lines if line.strip()]})
    
    async def _profile_data_intelligently(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Intelligent data profiling to understand business context
        """
        profile = {
            'filename': filename,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'unique_counts': df.nunique().to_dict(),
            'business_context': {},
            'data_patterns': {}
        }
        
        # Analyze each column for business meaning
        for col in df.columns:
            col_analysis = await self._analyze_column_meaning(df[col], col, filename)
            profile['business_context'][col] = col_analysis
        
        # Detect overall dataset purpose using LLM
        dataset_purpose = await self._detect_dataset_purpose(df, filename)
        profile['dataset_purpose'] = dataset_purpose
        
        return profile
    
    async def _analyze_column_meaning(self, series: pd.Series, col_name: str, filename: str) -> Dict[str, Any]:
        """
        Analyze what a column represents in business terms
        """
        analysis = {
            'original_name': col_name,
            'data_type': str(series.dtype),
            'business_type': 'unknown',
            'description': '',
            'examples': series.dropna().head(3).tolist() if not series.empty else []
        }
        
        # Pattern recognition for common business data types
        col_lower = col_name.lower()
        sample_values = series.dropna().astype(str).head(10).tolist()
        
        # Email detection
        if any('@' in str(val) for val in sample_values):
            analysis['business_type'] = 'email'
            analysis['description'] = 'Email address'
        
        # Date detection
        elif series.dtype.name.startswith('datetime') or 'date' in col_lower or 'time' in col_lower:
            analysis['business_type'] = 'date'
            analysis['description'] = 'Date or timestamp'
        
        # ID detection
        elif 'id' in col_lower or col_lower.endswith('_id') or col_lower.startswith('id_'):
            analysis['business_type'] = 'identifier'
            analysis['description'] = 'Unique identifier'
        
        # Money/currency detection
        elif ('price' in col_lower or 'cost' in col_lower or 'amount' in col_lower or 
              'revenue' in col_lower or 'salary' in col_lower or '$' in str(sample_values[0] if sample_values else '')):
            analysis['business_type'] = 'currency'
            analysis['description'] = 'Monetary amount'
        
        # Name detection
        elif 'name' in col_lower or 'title' in col_lower:
            analysis['business_type'] = 'name'
            analysis['description'] = 'Name or title'
        
        # Status/category detection
        elif series.nunique() < 10 and series.dtype == 'object':
            analysis['business_type'] = 'category'
            analysis['description'] = f'Categorical data with {series.nunique()} unique values'
        
        # Numeric metrics
        elif pd.api.types.is_numeric_dtype(series):
            if series.nunique() == len(series):  # Likely continuous
                analysis['business_type'] = 'metric'
                analysis['description'] = 'Numerical metric or measurement'
            else:  # Likely discrete counts
                analysis['business_type'] = 'count'
                analysis['description'] = 'Count or discrete number'
        
        return analysis
    
    async def _detect_dataset_purpose(self, df: pd.DataFrame, filename: str) -> str:
        """
        Use LLM to understand the overall purpose of the dataset
        """
        # Create a data summary for LLM analysis
        summary = {
            'filename': filename,
            'columns': list(df.columns),
            'shape': df.shape,
            'sample_data': df.head(2).to_dict('records') if not df.empty else []
        }
        
        prompt = f"""
        Analyze this dataset and determine its business purpose in 1-2 sentences:
        
        Filename: {filename}
        Columns: {', '.join(df.columns)}
        Rows: {df.shape[0]}
        Sample data: {json.dumps(summary['sample_data'], default=str)}
        
        What type of business data is this and what questions might users want to ask about it?
        """
        
        try:
            purpose = await self.llm_service.generate_response(prompt)
            return purpose.strip()
        except:
            return f"Dataset with {df.shape[0]} rows and {df.shape[1]} columns"
    
    async def _adaptive_data_cleaning(self, df: pd.DataFrame, profile: Dict[str, Any]) -> pd.DataFrame:
        """
        Intelligently clean data based on its detected characteristics
        """
        cleaned_df = df.copy()
        
        for col in cleaned_df.columns:
            col_info = profile['business_context'].get(col, {})
            business_type = col_info.get('business_type', 'unknown')
            
            # Type-specific cleaning
            if business_type == 'currency':
                # Clean currency symbols and convert to numeric
                cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
            
            elif business_type == 'date':
                # Standardize date formats
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
            
            elif business_type == 'category':
                # Standardize categorical values
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.lower()
            
            elif business_type == 'email':
                # Standardize email format
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.lower()
        
        return cleaned_df
    
    async def _generate_business_schema(self, df: pd.DataFrame, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate business-friendly schema with descriptions
        """
        schema = {}
        
        for col in df.columns:
            col_info = profile['business_context'].get(col, {})
            
            # Create business-friendly column name
            friendly_name = col.replace('_', ' ').title()
            
            schema[col] = {
                'display_name': friendly_name,
                'data_type': str(df[col].dtype),
                'business_type': col_info.get('business_type', 'text'),
                'description': col_info.get('description', f'{friendly_name} column'),
                'nullable': df[col].isnull().any(),
                'unique_values': int(df[col].nunique()),
                'examples': df[col].dropna().head(3).tolist() if not df[col].empty else []
            }
        
        return schema
    
    async def _generate_adaptive_questions(self, df: pd.DataFrame, schema: Dict[str, Any], 
                                         profile: Dict[str, Any]) -> List[str]:
        """
        Generate contextually relevant questions based on the data
        """
        # Analyze data characteristics
        has_dates = any(info.get('business_type') == 'date' for info in schema.values())
        has_categories = any(info.get('business_type') == 'category' for info in schema.values())
        has_metrics = any(info.get('business_type') in ['metric', 'currency', 'count'] 
                         for info in schema.values())
        
        questions = []
        
        # Generic questions
        questions.append(f"How many records are in this dataset?")
        
        if has_categories:
            # Find categorical columns
            cat_cols = [col for col, info in schema.items() 
                       if info.get('business_type') == 'category']
            for col in cat_cols[:2]:  # Limit to first 2
                display_name = schema[col]['display_name']
                questions.append(f"Show me the distribution of {display_name}")
        
        if has_metrics:
            # Find metric columns
            metric_cols = [col for col, info in schema.items() 
                          if info.get('business_type') in ['metric', 'currency', 'count']]
            for col in metric_cols[:2]:  # Limit to first 2
                display_name = schema[col]['display_name']
                questions.append(f"What is the average {display_name}?")
        
        if has_dates and has_metrics:
            # Time-based questions
            questions.append("Show me trends over time")
        
        # Use LLM to generate more specific questions
        try:
            context_prompt = f"""
            Based on this dataset structure, generate 3 relevant business questions:
            
            Dataset purpose: {profile.get('dataset_purpose', 'Unknown')}
            Columns: {list(schema.keys())}
            
            Generate specific, actionable questions that a business user would ask.
            """
            
            llm_questions = await self.llm_service.generate_response(context_prompt)
            # Parse LLM response into individual questions
            llm_question_list = [q.strip() for q in llm_questions.split('\n') 
                               if q.strip() and '?' in q][:3]
            questions.extend(llm_question_list)
        except:
            pass
        
        return questions[:8]  # Limit to 8 questions
    
    async def _store_adaptive_data(self, df: pd.DataFrame, schema: Dict[str, Any], 
                                 filename: str) -> str:
        """
        Store data with dynamically created table structure
        """
        # Generate unique table name
        base_name = re.sub(r'[^a-zA-Z0-9_]', '_', Path(filename).stem.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"data_{base_name}_{timestamp}"
        
        # Here we would create the dynamic table and insert data
        # For now, we'll use a generic approach
        
        try:
            # Convert DataFrame to the format expected by the database
            # This is a simplified version - in production, you'd want to create
            # actual dynamic tables based on the schema
            
            # Store metadata about the dynamic structure
            logger.info(f"Would create dynamic table: {table_name}")
            logger.info(f"Schema: {json.dumps(schema, indent=2, default=str)}")
            
            return table_name
            
        except Exception as e:
            logger.error(f"Error storing adaptive data: {str(e)}")
            raise