"""
Enhanced data source endpoints for Local AI-BI Platform
Handles files, databases, APIs, and HDFS connections
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
import os
import logging
import aiofiles

from app.database import get_db, DataSource, Dataset, AsyncSessionLocal
from app.services.enhanced_data_ingestion import EnhancedDataIngestionService
from app.services.adaptive_data_processor import AdaptiveDataProcessor
from app.services.realtime_data_processor import realtime_processor
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


async def process_adaptive_file(file_path: str, original_filename: str, display_name: str, 
                               file_size: int, content_type: str):
    """
    Background task to process uploaded file with adaptive intelligence
    """
    try:
        # Create new database session for background task
        async with AsyncSessionLocal() as db:
            # Create data source record
            data_source = DataSource(
                name=display_name,
                original_filename=original_filename,
                file_type=content_type or 'unknown',
                file_size=file_size,
                processing_status='processing'
            )
            db.add(data_source)
            await db.commit()
            await db.refresh(data_source)
            
            # Process with adaptive processor
            processor = AdaptiveDataProcessor()
            result = await processor.process_any_data(file_path, original_filename)
            
            if result['success']:
                # Update data source with results
                data_source.processing_status = 'completed'
                data_source.row_count = result['row_count']
                data_source.column_count = result['column_count']
                data_source.schema_info = result['schema']
                
                # Create dataset record
                dataset = Dataset(
                    data_source_id=data_source.id,
                    table_name=result['table_name'],
                    display_name=display_name,
                    description=result['profile'].get('dataset_purpose', f'Dataset from {original_filename}'),
                    schema_definition=result['schema'],
                    sample_questions=result['sample_questions']
                )
                db.add(dataset)
                
            else:
                # Mark as failed
                data_source.processing_status = 'failed'
                
            await db.commit()
            logger.info(f"Adaptive processing completed for {original_filename}")
        
    except Exception as e:
        logger.error(f"Adaptive processing failed for {original_filename}: {str(e)}")
        try:
            async with AsyncSessionLocal() as db:
                data_source = await db.get(DataSource, data_source.id)
                if data_source:
                    data_source.processing_status = 'failed'
                    await db.commit()
        except:
            pass


class DatabaseSourceConfig(BaseModel):
    """Database connection configuration"""
    connection_string: str = Field(..., description="Database connection string")
    table: Optional[str] = Field(None, description="Table name to import")
    query: Optional[str] = Field(None, description="Custom SQL query")
    limit: Optional[int] = Field(1000, description="Row limit for import")


class APISourceConfig(BaseModel):
    """API data source configuration"""
    url: str = Field(..., description="API endpoint URL")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    params: Optional[Dict[str, str]] = Field(None, description="Query parameters")
    auth: Optional[Dict[str, Any]] = Field(None, description="Authentication config")
    timeout: Optional[int] = Field(30, description="Request timeout in seconds")


class HDFSSourceConfig(BaseModel):
    """HDFS data source configuration"""
    path: str = Field(..., description="HDFS file path")
    format: Optional[str] = Field("parquet", description="File format (parquet, csv)")


class DataSourceRequest(BaseModel):
    """Universal data source request"""
    name: str = Field(..., description="Human-readable name for the data source")
    type: str = Field(..., description="Data source type: file, database, api, hdfs")
    database_config: Optional[DatabaseSourceConfig] = None
    api_config: Optional[APISourceConfig] = None
    hdfs_config: Optional[HDFSSourceConfig] = None


@router.post("/file", response_model=Dict[str, Any])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a data file with real-time status updates"""
    
    try:
        # Read file content
        content = await file.read()
        await file.seek(0)
        
        # Validate file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Start real-time processing
        async def process_with_updates():
            async with AsyncSessionLocal() as session:
                await realtime_processor.process_file_with_updates(
                    file_path=file_path,
                    filename=file.filename,
                    file_type=file.content_type or 'application/octet-stream',
                    file_size=len(content),
                    user_id=user_id,
                    db=session
                )
        
        # Add to background tasks
        background_tasks.add_task(process_with_updates)
        
        logger.info(f"File uploaded: {file.filename} ({len(content)} bytes)")
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "status": "processing",
            "message": "File uploaded successfully. Processing started with real-time updates.",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/database", response_model=Dict[str, Any])
async def connect_database(
    config: DatabaseSourceConfig,
    name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Connect to and import data from a database"""
    
    try:
        # Prepare source configuration
        source_config = {
            "type": "database",
            "source": config.connection_string,
            "name": name,
            "options": {
                "table": config.table,
                "query": config.query,
                "limit": config.limit
            }
        }
        
        # Process database source in background
        ingestion_service = EnhancedDataIngestionService()
        background_tasks.add_task(
            ingestion_service.process_data_source,
            source_config,
            db
        )
        
        logger.info(f"Database connection initiated: {name}")
        
        return {
            "success": True,
            "name": name,
            "status": "processing",
            "message": "Database connection established and import started"
        }
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@router.post("/api", response_model=Dict[str, Any])
async def connect_api(
    config: APISourceConfig,
    name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Connect to and import data from an API"""
    
    try:
        # Prepare source configuration
        source_config = {
            "type": "api",
            "source": config.url,
            "name": name,
            "options": {
                "headers": config.headers or {},
                "params": config.params or {},
                "auth": config.auth,
                "timeout": config.timeout
            }
        }
        
        # Process API source in background
        ingestion_service = EnhancedDataIngestionService()
        background_tasks.add_task(
            ingestion_service.process_data_source,
            source_config,
            db
        )
        
        logger.info(f"API connection initiated: {name}")
        
        return {
            "success": True,
            "name": name,
            "status": "processing",
            "message": "API connection established and import started"
        }
        
    except Exception as e:
        logger.error(f"API connection failed: {e}")
        raise HTTPException(status_code=500, detail="API connection failed")


@router.post("/hdfs", response_model=Dict[str, Any])
async def connect_hdfs(
    config: HDFSSourceConfig,
    name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Connect to and import data from HDFS"""
    
    try:
        # Prepare source configuration
        source_config = {
            "type": "hdfs",
            "source": config.path,
            "name": name,
            "options": {
                "format": config.format
            }
        }
        
        # Process HDFS source in background
        ingestion_service = EnhancedDataIngestionService()
        background_tasks.add_task(
            ingestion_service.process_data_source,
            source_config,
            db
        )
        
        logger.info(f"HDFS connection initiated: {name}")
        
        return {
            "success": True,
            "name": name,
            "status": "processing",
            "message": "HDFS connection established and import started"
        }
        
    except Exception as e:
        logger.error(f"HDFS connection failed: {e}")
        raise HTTPException(status_code=500, detail="HDFS connection failed")


@router.get("/sources", response_model=List[Dict[str, Any]])
async def list_data_sources(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all data sources with optional status filter"""
    
    try:
        from sqlalchemy import select
        
        query = select(DataSource)
        if status:
            query = query.where(DataSource.processing_status == status)
        
        result = await db.execute(query.order_by(DataSource.created_at.desc()))
        data_sources = result.scalars().all()
        
        return [
            {
                "id": str(ds.id),
                "name": ds.name,
                "type": ds.file_type,
                "status": ds.processing_status,
                "row_count": ds.row_count,
                "column_count": ds.column_count,
                "created_at": ds.created_at.isoformat(),
                "updated_at": ds.updated_at.isoformat()
            }
            for ds in data_sources
        ]
        
    except Exception as e:
        logger.error(f"Failed to list data sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to list data sources")


@router.get("/source/{data_source_id}", response_model=Dict[str, Any])
async def get_data_source(
    data_source_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a data source"""
    
    try:
        # Get data source
        data_source = await db.get(DataSource, uuid.UUID(data_source_id))
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        # Get associated dataset
        from sqlalchemy import select
        result = await db.execute(
            select(Dataset).where(Dataset.data_source_id == data_source.id)
        )
        dataset = result.scalar_one_or_none()
        
        response = {
            "id": str(data_source.id),
            "name": data_source.name,
            "original_filename": data_source.original_filename,
            "type": data_source.file_type,
            "status": data_source.processing_status,
            "file_size": data_source.file_size,
            "row_count": data_source.row_count,
            "column_count": data_source.column_count,
            "schema": data_source.schema_info,
            "created_at": data_source.created_at.isoformat(),
            "updated_at": data_source.updated_at.isoformat()
        }
        
        if dataset:
            response.update({
                "dataset_id": str(dataset.id),
                "table_name": dataset.table_name,
                "sample_questions": dataset.sample_questions
            })
        
        return response
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data source ID")
    except Exception as e:
        logger.error(f"Failed to get data source: {e}")
        raise HTTPException(status_code=500, detail="Failed to get data source")


@router.get("/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get upload processing status (legacy endpoint)"""
    
    try:
        data_source_id = uuid.UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload ID")
    
    # Query data source
    data_source = await db.get(DataSource, data_source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return {
        "id": str(data_source.id),
        "filename": data_source.original_filename,
        "status": data_source.processing_status,
        "row_count": data_source.row_count,
        "column_count": data_source.column_count,
        "upload_date": data_source.upload_date.isoformat(),
        "schema_info": data_source.schema_info
    }


@router.get("/history")
async def get_upload_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent upload history (legacy endpoint)"""
    
    from sqlalchemy import select, desc
    
    query = select(DataSource).order_by(desc(DataSource.upload_date)).limit(limit)
    result = await db.execute(query)
    data_sources = result.scalars().all()
    
    return [
        {
            "id": str(ds.id),
            "name": ds.name,
            "filename": ds.original_filename,
            "status": ds.processing_status,
            "upload_date": ds.upload_date.isoformat(),
            "row_count": ds.row_count,
            "column_count": ds.column_count
        }
        for ds in data_sources
    ]


@router.get("/datasets", response_model=List[Dict[str, Any]])
async def list_datasets(
    db: AsyncSession = Depends(get_db)
):
    """List all available datasets for querying"""
    
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(Dataset)
            .join(DataSource)
            .where(DataSource.processing_status == "completed")
            .order_by(Dataset.created_at.desc())
        )
        datasets = result.scalars().all()
        
        return [
            {
                "id": str(dataset.id),
                "name": dataset.display_name,
                "description": dataset.description,
                "table_name": dataset.table_name,
                "sample_questions": dataset.sample_questions,
                "schema": dataset.schema_definition,
                "created_at": dataset.created_at.isoformat()
            }
            for dataset in datasets
        ]
        
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail="Failed to list datasets")


@router.delete("/source/{data_source_id}")
async def delete_data_source(
    data_source_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a data source and its associated data"""
    
    try:
        # Get data source
        data_source = await db.get(DataSource, uuid.UUID(data_source_id))
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        # Get associated dataset
        from sqlalchemy import select, delete
        result = await db.execute(
            select(Dataset).where(Dataset.data_source_id == data_source.id)
        )
        dataset = result.scalar_one_or_none()
        
        # Drop database table if it exists
        if dataset:
            try:
                await db.execute(text(f"DROP TABLE IF EXISTS {dataset.table_name}"))
            except:
                pass  # Table might not exist
        
        # Delete dataset record
        if dataset:
            await db.execute(
                delete(Dataset).where(Dataset.data_source_id == data_source.id)
            )
        
        # Delete data source record
        await db.delete(data_source)
        await db.commit()
        
        logger.info(f"Deleted data source: {data_source.name}")
        
        return {
            "success": True,
            "message": "Data source deleted successfully"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data source ID")
    except Exception as e:
        logger.error(f"Failed to delete data source: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete data source")