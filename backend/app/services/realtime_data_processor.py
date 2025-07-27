"""
Real-time Data Processing Service with WebSocket Integration
Provides live status updates during data ingestion and analysis
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.enhanced_data_ingestion import EnhancedDataIngestionService
from app.services.websocket_manager import websocket_manager
from app.database import DataSource, Dataset

logger = logging.getLogger(__name__)


class RealtimeDataProcessor:
    """Real-time data processor with live status updates"""
    
    def __init__(self):
        self.ingestion_service = EnhancedDataIngestionService()
    
    async def process_file_with_updates(
        self,
        file_path: str,
        filename: str,
        file_type: str,
        file_size: int,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process uploaded file with real-time status updates"""
        
        # Create data source record
        data_source = DataSource(
            name=filename.replace('.', '_').replace('-', '_'),
            original_filename=filename,
            file_type=file_type,
            file_size=file_size,
            processing_status="analyzing"
        )
        
        db.add(data_source)
        await db.commit()
        await db.refresh(data_source)
        
        data_source_id = str(data_source.id)
        
        try:
            # Send initial status
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="analyzing",
                progress=10,
                message="🔍 Analyzing file format and structure...",
                details={"filename": filename, "size": file_size}
            )
            
            # Step 1: File format detection and initial analysis
            await asyncio.sleep(0.5)  # Brief pause for UI feedback
            
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="reading",
                progress=25,
                message="📖 Reading and parsing file data...",
                details={"detected_format": file_type}
            )
            
            # Configure source for processing
            source_config = {
                'type': 'file',
                'source': file_path,
                'name': data_source.name,
                'options': {'format': file_type}
            }
            
            # Step 2: Data extraction and loading
            df = await self.ingestion_service._process_file_source(source_config)
            
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="cleaning",
                progress=40,
                message="🧹 Cleaning and preparing data...",
                details={
                    "raw_rows": len(df),
                    "raw_columns": len(df.columns)
                }
            )
            
            # Step 3: Data cleaning with progress updates
            df_cleaned = await self._clean_with_progress(df, user_id, data_source_id)
            
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="analyzing_schema",
                progress=65,
                message="🔬 Analyzing data structure and generating schema...",
                details={
                    "cleaned_rows": len(df_cleaned),
                    "cleaned_columns": len(df_cleaned.columns)
                }
            )
            
            # Step 4: Schema generation with intelligence
            schema_info = await self._generate_schema_with_insights(
                df_cleaned, source_config, user_id, data_source_id
            )
            
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="storing",
                progress=80,
                message="💾 Creating database table and storing data...",
                details={"schema_generated": True}
            )
            
            # Step 5: Database storage
            table_name = self.ingestion_service._generate_table_name(data_source.name)
            await self.ingestion_service._create_database_table(df_cleaned, table_name, db)
            
            # Step 6: Generate intelligent questions
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="generating_insights",
                progress=90,
                message="🧠 Generating sample questions and insights...",
                details={"table_created": table_name}
            )
            
            sample_questions = await self.ingestion_service._generate_intelligent_questions(
                schema_info, data_source.name, df_cleaned
            )
            
            # Update data source
            data_source.processing_status = "completed"
            data_source.row_count = len(df_cleaned)
            data_source.column_count = len(df_cleaned.columns)
            data_source.schema_info = schema_info
            
            # Create dataset record
            dataset = Dataset(
                data_source_id=data_source.id,
                table_name=table_name,
                display_name=data_source.name,
                description=f"Processed data from {filename}",
                schema_definition=schema_info,
                sample_questions=sample_questions
            )
            
            db.add(dataset)
            await db.commit()
            
            # Final success update
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="completed",
                progress=100,
                message="✅ Data processing completed successfully!",
                details={
                    "final_rows": len(df_cleaned),
                    "final_columns": len(df_cleaned.columns),
                    "table_name": table_name,
                    "sample_questions_count": len(sample_questions),
                    "dataset_id": str(dataset.id)
                }
            )
            
            # Send data insights summary
            insights = await self._generate_data_insights(df_cleaned, schema_info)
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="insights_ready",
                progress=100,
                message="📊 Data insights generated",
                details={"insights": insights}
            )
            
            return {
                "success": True,
                "data_source_id": data_source_id,
                "dataset_id": str(dataset.id),
                "table_name": table_name,
                "row_count": len(df_cleaned),
                "column_count": len(df_cleaned.columns),
                "schema": schema_info,
                "sample_questions": sample_questions,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Processing failed for {filename}: {e}")
            
            # Update status to failed
            data_source.processing_status = "failed"
            await db.commit()
            
            # Send error update
            await websocket_manager.send_data_processing_update(
                user_id=user_id,
                data_source_id=data_source_id,
                status="failed",
                progress=0,
                message=f"❌ Processing failed: {str(e)}",
                details={"error": str(e)}
            )
            
            raise
    
    async def _clean_with_progress(self, df, user_id: str, data_source_id: str):
        """Data cleaning with progress updates"""
        
        # Step 1: Remove empty rows/columns
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="cleaning",
            progress=42,
            message="Removing empty rows and columns..."
        )
        
        df_clean = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Step 2: Clean column names
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="cleaning", 
            progress=45,
            message="Standardizing column names..."
        )
        
        df_clean.columns = [
            self.ingestion_service._clean_column_name(col) for col in df_clean.columns
        ]
        
        # Step 3: Handle duplicates
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="cleaning",
            progress=50,
            message="Detecting and handling duplicate data..."
        )
        
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        duplicates_removed = initial_rows - len(df_clean)
        
        # Step 4: Type inference
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="cleaning",
            progress=55,
            message="Detecting and converting data types...",
            details={"duplicates_removed": duplicates_removed}
        )
        
        df_clean = await self.ingestion_service._enhanced_type_inference(df_clean)
        
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="cleaning",
            progress=60,
            message="Data cleaning completed successfully",
            details={
                "final_rows": len(df_clean),
                "final_columns": len(df_clean.columns),
                "duplicates_removed": duplicates_removed
            }
        )
        
        return df_clean
    
    async def _generate_schema_with_insights(self, df, config, user_id: str, data_source_id: str):
        """Generate schema with detailed insights"""
        
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="analyzing_schema",
            progress=70,
            message="Analyzing column types and patterns..."
        )
        
        schema = await self.ingestion_service._generate_enhanced_schema(df, config)
        
        await websocket_manager.send_data_processing_update(
            user_id=user_id,
            data_source_id=data_source_id,
            status="analyzing_schema",
            progress=75,
            message="Generating business intelligence insights...",
            details={"columns_analyzed": len(schema)}
        )
        
        return schema
    
    async def _generate_data_insights(self, df, schema) -> Dict[str, Any]:
        """Generate comprehensive data insights"""
        
        insights = {
            "overview": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                "completeness_score": round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 1)
            },
            "column_types": {},
            "data_quality": {},
            "business_insights": [],
            "recommendations": []
        }
        
        # Column type distribution
        type_counts = {}
        for col_info in schema.values():
            col_type = col_info['type']
            type_counts[col_type] = type_counts.get(col_type, 0) + 1
        insights["column_types"] = type_counts
        
        # Data quality assessment
        quality_issues = []
        high_quality_cols = []
        
        for col, col_info in schema.items():
            quality_score = col_info.get('data_quality_score', 0)
            missing_pct = col_info.get('missing_percentage', 0)
            
            if quality_score < 50:
                quality_issues.append(f"{col}: {quality_score:.1f}% quality")
            elif quality_score > 90:
                high_quality_cols.append(col)
            
            if missing_pct > 20:
                quality_issues.append(f"{col}: {missing_pct:.1f}% missing values")
        
        insights["data_quality"] = {
            "high_quality_columns": len(high_quality_cols),
            "quality_issues": quality_issues[:5],  # Top 5 issues
            "overall_score": round(sum(col_info.get('data_quality_score', 0) for col_info in schema.values()) / len(schema), 1)
        }
        
        # Business insights
        numeric_cols = [col for col, info in schema.items() if info['type'] in ['number', 'currency']]
        categorical_cols = [col for col, info in schema.items() if info['type'] == 'category']
        
        if numeric_cols:
            insights["business_insights"].append(f"📊 Found {len(numeric_cols)} numeric columns for quantitative analysis")
        
        if categorical_cols:
            insights["business_insights"].append(f"🏷️ Found {len(categorical_cols)} categorical columns for segmentation")
        
        if any('date' in col.lower() for col in df.columns):
            insights["business_insights"].append("📅 Time-based analysis possible with date columns")
        
        if any('customer' in col.lower() for col in df.columns):
            insights["business_insights"].append("👥 Customer analysis capabilities detected")
        
        if any(term in ' '.join(df.columns).lower() for term in ['revenue', 'sales', 'profit']):
            insights["business_insights"].append("💰 Financial analysis opportunities identified")
        
        # Recommendations
        if len(quality_issues) > 0:
            insights["recommendations"].append("Consider cleaning data quality issues before analysis")
        
        if len(numeric_cols) > 0 and len(categorical_cols) > 0:
            insights["recommendations"].append("Cross-tabulation analysis recommended between numeric and categorical data")
        
        if insights["overview"]["completeness_score"] < 80:
            insights["recommendations"].append("Review missing data patterns before drawing conclusions")
        
        return insights


# Global instance
realtime_processor = RealtimeDataProcessor()