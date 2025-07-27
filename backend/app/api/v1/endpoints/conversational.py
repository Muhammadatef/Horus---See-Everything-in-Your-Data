"""
Conversational AI endpoint for single-step file analysis
Mimics ChatGPT/Claude behavior with file + question together
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import tempfile
import os
import uuid
import logging

from app.database import AsyncSessionLocal
from app.services.enhanced_data_ingestion import EnhancedDataIngestionService
from app.services.enhanced_llm_service import EnhancedLLMService
from app.services.advanced_analysis_service import AdvancedAnalysisService
from app.services.conversation_memory_service import conversation_memory

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency for database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/analyze")
async def analyze_file_with_question(
    file: UploadFile = File(...),
    question: str = Form(...),
    user_id: str = Form(default="default"),
    conversation_id: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Conversational file analysis - upload file and ask question in one step
    Returns ChatGPT/Claude-style response with context and follow-ups
    """
    
    try:
        # Generate conversation ID if not provided or create new conversation
        if not conversation_id:
            conversation_id = conversation_memory.create_conversation(
                user_id=user_id,
                file_info={'filename': file.filename, 'content_type': file.content_type}
            )
            logger.info(f"Created new conversation {conversation_id}")
        else:
            # Check if conversation exists
            context = conversation_memory.get_conversation_context(conversation_id)
            if not context:
                logger.warning(f"Conversation {conversation_id} not found, creating new one")
                conversation_id = conversation_memory.create_conversation(
                    user_id=user_id,
                    file_info={'filename': file.filename, 'content_type': file.content_type}
                )
        
        # Add user message to conversation history
        conversation_memory.add_message(conversation_id, 'user', question)
        
        logger.info(f"Processing question in conversation {conversation_id}: {question}")
        
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Initialize services
        ingestion_service = EnhancedDataIngestionService()
        llm_service = EnhancedLLMService()
        advanced_analysis = AdvancedAnalysisService()
        
        # Step 1: Quick data ingestion and analysis
        source_config = {
            'source_type': 'file',
            'source': temp_file_path,
            'options': {
                'format': file.content_type if file.content_type != 'application/octet-stream' else None
            }
        }
        
        # Process file data
        df = await ingestion_service._process_file_source(source_config)
        logger.info(f"Processed {len(df)} rows with {len(df.columns)} columns")
        
        # Generate enhanced schema
        schema = await ingestion_service._generate_enhanced_schema(df, source_config)
        
        # Step 2: Perform SOPHISTICATED ANALYSIS
        logger.info(f"🔬 Starting advanced analysis for question: {question}")
        
        # Get all data for comprehensive analysis (not just sample)
        all_data = df.to_dict('records')
        
        # Perform advanced data science analysis
        advanced_results = await advanced_analysis.analyze_with_sophistication(
            data=all_data,
            question=question,
            schema=schema
        )
        
        # Update conversation with data context
        conversation_memory.update_data_context(
            conversation_id, 
            schema, 
            {'total_rows': len(df), 'columns': len(df.columns)}
        )
        
        # Get conversation context for LLM
        conversation_context = conversation_memory.get_conversation_context(conversation_id)
        
        # Generate sophisticated conversational response with context
        answer = await llm_service._generate_advanced_conversational_response(
            question=question,
            advanced_analysis_results=advanced_results,
            schema=schema,
            file_info={
                'filename': file.filename,
                'total_rows': len(df),
                'columns': len(df.columns)
            },
            conversation_context=conversation_context
        )
        
        # Generate intelligent follow-up questions based on analysis
        follow_ups = await llm_service._generate_intelligent_follow_ups(
            question=question,
            analysis_results=advanced_results,
            schema=schema
        )
        
        # Create sophisticated visualizations based on analysis type
        visualization = await advanced_analysis._generate_advanced_visualizations(
            advanced_results, question, df.to_dict('records')
        )
        
        # Add assistant's response to conversation memory
        conversation_memory.add_message(
            conversation_id, 
            'assistant', 
            answer,
            analysis_results=advanced_results,
            visualization=visualization
        )
        
        response = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "data_summary": {
                "filename": file.filename,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "sample_data": all_data[:3]  # Just first 3 rows
            },
            "visualization": visualization,
            "follow_up_questions": follow_ups,
            "conversation_context": {
                "file_analyzed": True,
                "data_schema": schema
            },
            "advanced_analysis": advanced_results,
            "success": True
        }
        
        # Cleanup
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Conversational analysis error: {e}")
        # Cleanup on error
        try:
            if 'temp_file_path' in locals():
                os.remove(temp_file_path)
            if 'temp_dir' in locals():
                os.rmdir(temp_dir)
        except:
            pass
        
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to analyze file: {str(e)}",
                "success": False
            }
        )

@router.post("/continue")
async def continue_conversation(
    question: str = Form(...),
    conversation_id: str = Form(...),
    user_id: str = Form(default="default"),
    db: AsyncSession = Depends(get_db)
):
    """
    Continue existing conversation with follow-up questions
    Uses conversation memory to maintain context like ChatGPT
    """
    
    try:
        # Validate conversation exists
        conversation_context = conversation_memory.get_conversation_context(conversation_id)
        if not conversation_context:
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"Conversation {conversation_id} not found",
                    "success": False
                }
            )
        
        # Add user message to conversation history
        conversation_memory.add_message(conversation_id, 'user', question)
        
        # Initialize services
        llm_service = EnhancedLLMService()
        advanced_analysis = AdvancedAnalysisService()
        
        # Get data from conversation context
        data_schema = conversation_context.get('data_schema', {})
        file_info = conversation_context.get('file_info', {})
        
        # For follow-up questions, we might need to re-analyze data or use cached results
        # For now, create a lightweight analysis based on context
        mock_analysis_results = {
            'statistical_overview': conversation_context.get('data_summary', {}),
            'conversation_context': True  # Flag to indicate this is a follow-up
        }
        
        # Generate contextual response using conversation history
        answer = await llm_service._generate_advanced_conversational_response(
            question=question,
            advanced_analysis_results=mock_analysis_results,
            schema=data_schema,
            file_info=file_info,
            conversation_context=conversation_context
        )
        
        # Generate intelligent follow-ups based on conversation context
        follow_ups = await llm_service._generate_intelligent_follow_ups(
            question=question,
            analysis_results=mock_analysis_results,
            schema=data_schema
        )
        
        # Add assistant's response to conversation memory
        conversation_memory.add_message(
            conversation_id, 
            'assistant', 
            answer
        )
        
        response = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "follow_up_questions": follow_ups,
            "conversation_summary": conversation_memory.get_conversation_summary(conversation_id),
            "success": True
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Conversation continuation error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to continue conversation: {str(e)}",
                "success": False
            }
        )