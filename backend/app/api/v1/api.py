"""
Main API router for Local AI-BI Platform
"""

from fastapi import APIRouter

from app.api.v1.endpoints import upload, query, data, health, websocket, conversational

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(conversational.router, prefix="/conversational", tags=["conversational"])
api_router.include_router(websocket.router, tags=["websocket"])