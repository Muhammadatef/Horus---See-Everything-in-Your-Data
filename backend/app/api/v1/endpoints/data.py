"""
Data management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Dict, Any
import uuid
import logging

from app.database import get_db, DataSource, Dataset
from app.services.query_engine import QueryEngine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sources")
async def list_data_sources(db: AsyncSession = Depends(get_db)):
    """List all uploaded data sources"""
    
    query = select(DataSource).order_by(DataSource.upload_date.desc())
    result = await db.execute(query)
    sources = result.scalars().all()
    
    return [
        {
            "id": str(source.id),
            "name": source.name,
            "filename": source.original_filename,
            "file_type": source.file_type,
            "status": source.processing_status,
            "row_count": source.row_count,
            "column_count": source.column_count,
            "upload_date": source.upload_date.isoformat()
        }
        for source in sources
    ]


@router.get("/datasets")
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """List all processed datasets ready for querying"""
    
    query = select(Dataset).order_by(Dataset.created_at.desc())
    result = await db.execute(query)
    datasets = result.scalars().all()
    
    return [
        {
            "id": str(dataset.id),
            "name": dataset.display_name,
            "table_name": dataset.table_name,
            "description": dataset.description,
            "sample_questions": dataset.sample_questions,
            "created_at": dataset.created_at.isoformat()
        }
        for dataset in datasets
    ]


@router.get("/datasets/{dataset_id}")
async def get_dataset_details(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific dataset"""
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    dataset = await db.get(Dataset, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get row count from actual table
    row_count = 0
    try:
        count_query = text(f"SELECT COUNT(*) FROM {dataset.table_name}")
        result = await db.execute(count_query)
        row_count = result.scalar()
    except Exception as e:
        logger.warning(f"Could not get row count for {dataset.table_name}: {e}")
    
    return {
        "id": str(dataset.id),
        "name": dataset.display_name,
        "table_name": dataset.table_name,
        "description": dataset.description,
        "schema_definition": dataset.schema_definition,
        "sample_questions": dataset.sample_questions,
        "row_count": row_count,
        "created_at": dataset.created_at.isoformat()
    }


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get a preview of dataset data"""
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    dataset = await db.get(Dataset, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Get sample data
        preview_query = text(f"SELECT * FROM {dataset.table_name} LIMIT :limit")
        result = await db.execute(preview_query, {"limit": limit})
        rows = result.fetchall()
        
        # Convert to list of dictionaries
        if rows:
            columns = list(rows[0]._fields)
            data = [dict(zip(columns, row)) for row in rows]
        else:
            columns = []
            data = []
        
        # Get total count
        count_query = text(f"SELECT COUNT(*) FROM {dataset.table_name}")
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        return {
            "columns": columns,
            "data": data,
            "total_rows": total_count,
            "preview_rows": len(data)
        }
        
    except Exception as e:
        logger.error(f"Preview error for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not preview dataset")


@router.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get schema information for a dataset"""
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    dataset = await db.get(Dataset, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "table_name": dataset.table_name,
        "schema_definition": dataset.schema_definition,
        "description": dataset.description
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a dataset and its associated data"""
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    dataset = await db.get(Dataset, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Drop the actual data table
        drop_query = text(f"DROP TABLE IF EXISTS {dataset.table_name}")
        await db.execute(drop_query)
        
        # Delete dataset record
        await db.delete(dataset)
        await db.commit()
        
        logger.info(f"Dataset deleted: {dataset.table_name}")
        
        return {"message": f"Dataset '{dataset.display_name}' deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete error for dataset {dataset_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete dataset")