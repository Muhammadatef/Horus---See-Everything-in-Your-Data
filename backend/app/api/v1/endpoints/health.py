"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import logging

from app.database import get_db
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "Local AI-BI Platform",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check including database and services"""
    health_status = {
        "service": "Local AI-BI Platform",
        "status": "healthy",
        "checks": {}
    }
    
    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Ollama LLM service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5.0)
            if response.status_code == 200:
                health_status["checks"]["llm"] = {"status": "healthy"}
            else:
                health_status["checks"]["llm"] = {"status": "unhealthy", "error": "Ollama not responding"}
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        health_status["checks"]["llm"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    return health_status