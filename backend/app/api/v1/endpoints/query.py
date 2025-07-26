"""
Natural language query endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import time
import logging

from app.database import get_db, Dataset, Query
from app.services.query_engine import QueryEngine
from app.services.llm_service import LLMService
from app.services.adaptive_query_engine import AdaptiveQueryEngine
from app.services.visualization_engine import visualization_engine
from app.services.websocket_manager import websocket_manager
from app.services.enhanced_query_processor import enhanced_query_processor

router = APIRouter()
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    dataset_id: str
    question: str
    user_id: str = "default"


class QueryResponse(BaseModel):
    id: str
    question: str
    answer: str
    sql: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    visualization: Optional[Dict[str, Any]] = None
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a natural language question about the data
    Returns answer with optional SQL and visualization
    """
    
    start_time = time.time()
    
    try:
        dataset_uuid = uuid.UUID(request.dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    # Get dataset
    dataset = await db.get(Dataset, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    query_record = Query(
        dataset_id=dataset_uuid,
        question=request.question,
        success=False
    )
    
    try:
        # Use enhanced query processor with real-time updates
        logger.info(f"Processing question with real-time updates: {request.question}")
        
        # Process with enhanced processor
        result = await enhanced_query_processor.process_query_with_updates(
            question=request.question,
            dataset_id=request.dataset_id,
            user_id=request.user_id,
            db=db
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        if result.get('success', False):
            # Update query record with results
            query_record.generated_sql = result.get('sql')
            query_record.results = result.get('results')
            query_record.visualization_config = result.get('visualization')
            query_record.execution_time_ms = execution_time
            query_record.success = True
            
            # Save query record
            db.add(query_record)
            await db.commit()
            await db.refresh(query_record)
            
            logger.info(f"Enhanced query completed successfully in {execution_time}ms")
            
            return QueryResponse(
                id=str(query_record.id),
                question=request.question,
                answer=result.get('answer', 'Query completed successfully'),
                sql=result.get('sql'),
                results=result.get('results'),
                visualization=result.get('visualization'),
                execution_time_ms=execution_time,
                success=True
            )
        else:
            # Handle enhanced processor failure
            error_msg = result.get('error', 'Unknown error in query processing')
            raise Exception(error_msg)
        
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        
        logger.error(f"Query failed: {error_msg}")
        
        query_record.execution_time_ms = execution_time
        query_record.error_message = error_msg
        query_record.success = False
        
        db.add(query_record)
        await db.commit()
        
        return QueryResponse(
            id=str(query_record.id),
            question=request.question,
            answer=f"I'm sorry, I couldn't process your question. Error: {error_msg}",
            execution_time_ms=execution_time,
            success=False,
            error_message=error_msg
        )


@router.get("/history/{dataset_id}")
async def get_query_history(
    dataset_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get query history for a dataset"""
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    from sqlalchemy import select, desc
    
    query = (
        select(Query)
        .where(Query.dataset_id == dataset_uuid)
        .order_by(desc(Query.created_at))
        .limit(limit)
    )
    
    result = await db.execute(query)
    queries = result.scalars().all()
    
    return [
        {
            "id": str(q.id),
            "question": q.question,
            "success": q.success,
            "execution_time_ms": q.execution_time_ms,
            "created_at": q.created_at.isoformat(),
            "results": q.results,
            "visualization_config": q.visualization_config
        }
        for q in queries
    ]


@router.get("/suggestions/{dataset_id}")
async def get_query_suggestions(
    dataset_id: str,
    partial_question: str = "",
    db: AsyncSession = Depends(get_db)
):
    """Get intelligent query suggestions for a dataset"""
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID")
    
    dataset = await db.get(Dataset, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Use enhanced query processor for intelligent suggestions
    suggestions = await enhanced_query_processor.get_intelligent_suggestions(
        dataset_id, partial_question, db
    )
    
    return {
        "dataset_name": dataset.display_name,
        "suggestions": suggestions
    }