"""
Data ingestion and processing service
Handles file uploads, data cleaning, and schema generation
"""

import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
import os
import json
import logging
from typing import Dict, Any, List, Optional

from app.database import DataSource, Dataset
from app.config import settings

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for processing uploaded data files"""
    
    def __init__(self):
        self.supported_formats = {
            'text/csv': self._process_csv,
            'application/vnd.ms-excel': self._process_excel,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': self._process_excel,
            'application/json': self._process_json,
            'application/parquet': self._process_parquet
        }
    
    async def process_uploaded_file(
        self, 
        data_source_id: uuid.UUID, 
        file_path: str, 
        db: AsyncSession
    ):
        """Main processing function for uploaded files"""
        
        try:
            # Get data source record
            data_source = await db.get(DataSource, data_source_id)
            if not data_source:
                logger.error(f"Data source not found: {data_source_id}")
                return
            
            logger.info(f"Processing file: {data_source.original_filename}")
            
            # Update status to processing
            data_source.processing_status = "processing"
            await db.commit()
            
            # Load and process data based on file type
            processor = self.supported_formats.get(data_source.file_type)
            if not processor:
                raise ValueError(f"Unsupported file type: {data_source.file_type}")
            
            # Process the file
            df = await processor(file_path)
            
            # Clean and prepare data
            df_cleaned = self._clean_data(df)
            
            # Generate schema
            schema_info = self._generate_schema(df_cleaned)
            
            # Create database table
            table_name = self._generate_table_name(data_source.name)
            await self._create_database_table(df_cleaned, table_name, db)
            
            # Update data source with processing results
            data_source.processing_status = "completed"
            data_source.row_count = len(df_cleaned)
            data_source.column_count = len(df_cleaned.columns)
            data_source.schema_info = schema_info
            
            # Create dataset record
            dataset = Dataset(
                data_source_id=data_source_id,
                table_name=table_name,
                display_name=data_source.name,
                description=f"Processed data from {data_source.original_filename}",
                schema_definition=schema_info,
                sample_questions=self._generate_sample_questions(schema_info, data_source.name)
            )
            
            db.add(dataset)
            await db.commit()
            
            logger.info(f"File processed successfully: {data_source.original_filename}")
            
        except Exception as e:
            logger.error(f"Processing failed for {data_source_id}: {e}")
            
            # Update status to failed
            if data_source:
                data_source.processing_status = "failed"
                await db.commit()
    
    async def _process_csv(self, file_path: str) -> pd.DataFrame:
        """Process CSV files with automatic delimiter detection"""
        
        # Try different delimiters
        delimiters = [',', ';', '\t', '|']
        
        for delimiter in delimiters:
            try:
                df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8')
                if len(df.columns) > 1:  # Valid CSV should have multiple columns
                    logger.info(f"CSV loaded with delimiter '{delimiter}'")
                    return df
            except:
                continue
        
        # Fallback to default pandas CSV reader
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            return df
        except Exception as e:
            logger.error(f"CSV processing failed: {e}")
            raise ValueError(f"Could not parse CSV file: {e}")
    
    async def _process_excel(self, file_path: str) -> pd.DataFrame:
        """Process Excel files (supports multiple sheets)"""
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            
            if len(excel_file.sheet_names) == 1:
                # Single sheet - read directly
                df = pd.read_excel(file_path, sheet_name=0)
            else:
                # Multiple sheets - combine or use first non-empty sheet
                largest_df = None
                max_rows = 0
                
                for sheet_name in excel_file.sheet_names:
                    sheet_df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if len(sheet_df) > max_rows:
                        max_rows = len(sheet_df)
                        largest_df = sheet_df
                
                df = largest_df if largest_df is not None else pd.DataFrame()
            
            logger.info(f"Excel loaded with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Excel processing failed: {e}")
            raise ValueError(f"Could not parse Excel file: {e}")
    
    async def _process_json(self, file_path: str) -> pd.DataFrame:
        """Process JSON files (supports nested structures)"""
        
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.json_normalize(data)
            elif isinstance(data, dict):
                if any(isinstance(v, list) for v in data.values()):
                    # Find the largest list in the dict
                    largest_key = max(data.keys(), key=lambda k: len(data[k]) if isinstance(data[k], list) else 0)
                    df = pd.json_normalize(data[largest_key])
                else:
                    df = pd.json_normalize([data])
            else:
                raise ValueError("JSON must be an object or array")
            
            logger.info(f"JSON loaded with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"JSON processing failed: {e}")
            raise ValueError(f"Could not parse JSON file: {e}")
    
    async def _process_parquet(self, file_path: str) -> pd.DataFrame:
        """Process Parquet files"""
        
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"Parquet loaded with {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Parquet processing failed: {e}")
            raise ValueError(f"Could not parse Parquet file: {e}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data for analysis"""
        
        logger.info("Starting data cleaning...")
        
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Remove completely empty rows and columns
        df_clean = df_clean.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names (remove spaces, special chars)
        df_clean.columns = [
            col.strip().lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_clean.columns
        ]
        
        # Handle duplicate column names
        cols = pd.Series(df_clean.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
        df_clean.columns = cols
        
        # Basic data type inference and conversion
        for col in df_clean.columns:
            # Try to convert to numeric
            if df_clean[col].dtype == 'object':
                # Check if it looks like a number
                numeric_sample = pd.to_numeric(df_clean[col].head(100), errors='coerce')
                if not numeric_sample.isna().all():
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                else:
                    # Check if it looks like a date
                    try:
                        date_sample = pd.to_datetime(df_clean[col].head(10), errors='coerce')
                        if not date_sample.isna().all():
                            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                    except:
                        pass
        
        # Remove duplicate rows
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        duplicates_removed = initial_rows - len(df_clean)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        logger.info(f"Data cleaning completed. Final shape: {df_clean.shape}")
        
        return df_clean
    
    def _generate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate schema information from DataFrame"""
        
        schema = {}
        
        for col in df.columns:
            col_info = {
                "type": self._infer_column_type(df[col]),
                "description": self._generate_column_description(col, df[col]),
                "nullable": df[col].isna().any(),
                "unique_values": min(df[col].nunique(), 10)  # Cap at 10 for display
            }
            
            # Add statistics for numeric columns
            if col_info["type"] == "number":
                col_info["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
                col_info["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
                col_info["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
            
            # Add sample values for categorical columns
            if col_info["type"] == "string" and df[col].nunique() <= 20:
                col_info["sample_values"] = df[col].dropna().unique()[:10].tolist()
            
            schema[col] = col_info
        
        return schema
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer the appropriate type for a column"""
        
        if pd.api.types.is_numeric_dtype(series):
            return "number"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "date"
        elif pd.api.types.is_bool_dtype(series):
            return "boolean"
        else:
            return "string"
    
    def _generate_column_description(self, col_name: str, series: pd.Series) -> str:
        """Generate a human-readable description for a column"""
        
        # Basic description based on column name patterns
        col_lower = col_name.lower()
        
        if 'id' in col_lower:
            return f"Unique identifier for {col_name.replace('_id', '').replace('id', '')}"
        elif 'name' in col_lower:
            return f"Name or title"
        elif 'email' in col_lower:
            return "Email address"
        elif 'date' in col_lower or 'time' in col_lower:
            return f"Date/time information"
        elif 'status' in col_lower:
            return "Status or state information"
        elif 'amount' in col_lower or 'price' in col_lower or 'cost' in col_lower:
            return "Monetary amount"
        elif 'count' in col_lower or 'number' in col_lower:
            return "Numeric count or quantity"
        else:
            return f"Data column: {col_name.replace('_', ' ').title()}"
    
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
        """Create database table and insert data"""
        
        logger.info(f"Creating table: {table_name}")
        
        # Generate CREATE TABLE statement
        columns = []
        for col in df.columns:
            col_type = self._get_sql_type(df[col])
            columns.append(f'"{col}" {col_type}')
        
        create_sql = f"""
        CREATE TABLE {table_name} (
            {', '.join(columns)}
        )
        """
        
        # Create table
        await db.execute(text(create_sql))
        
        # Insert data in batches
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]
            
            # Prepare insert statement
            placeholders = ', '.join([f':{col}' for col in df.columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join([f'\"{col}\"' for col in df.columns])}) VALUES ({placeholders})"
            
            # Convert batch to records
            records = batch.to_dict('records')
            
            # Execute batch insert
            await db.execute(text(insert_sql), records)
        
        await db.commit()
        logger.info(f"Inserted {len(df)} rows into {table_name}")
    
    def _get_sql_type(self, series: pd.Series) -> str:
        """Map pandas dtype to SQL type"""
        
        if pd.api.types.is_integer_dtype(series):
            return "INTEGER"
        elif pd.api.types.is_float_dtype(series):
            return "DECIMAL"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "TIMESTAMP"
        elif pd.api.types.is_bool_dtype(series):
            return "BOOLEAN"
        else:
            return "TEXT"
    
    def _generate_sample_questions(self, schema: Dict[str, Any], dataset_name: str) -> List[str]:
        """Generate sample questions based on schema"""
        
        questions = []
        
        # Generic questions
        questions.append("How many records are in this dataset?")
        questions.append("Show me a summary of the data")
        
        # Questions based on columns
        for col_name, col_info in schema.items():
            col_display = col_name.replace('_', ' ').title()
            
            if col_info["type"] == "number":
                questions.append(f"What is the average {col_display}?")
                questions.append(f"Show me the distribution of {col_display}")
            
            elif col_info["type"] == "string" and col_info.get("unique_values", 0) < 20:
                questions.append(f"How many records by {col_display}?")
                questions.append(f"Show me the breakdown of {col_display}")
            
            elif "status" in col_name.lower():
                questions.append(f"How many active records are there?")
                questions.append(f"Show me the status distribution")
        
        return questions[:8]  # Limit to 8 questions