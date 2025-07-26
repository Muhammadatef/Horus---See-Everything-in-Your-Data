"""
WebSocket manager for real-time communication
Handles broadcasting status updates during data processing
"""

import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = "default"):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        
        # Send initial connection confirmation
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": self._get_timestamp()
        })
    
    def disconnect(self, connection_id: str, user_id: str = "default"):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(connection_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to connection {connection_id}: {e}")
                # Remove broken connection
                self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections for a user"""
        if user_id in self.user_sessions:
            connections = list(self.user_sessions[user_id])  # Copy to avoid modification during iteration
            for connection_id in connections:
                await self.send_to_connection(connection_id, message)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        if not self.active_connections:
            return
        
        connections = list(self.active_connections.keys())  # Copy to avoid modification during iteration
        for connection_id in connections:
            await self.send_to_connection(connection_id, message)
    
    async def send_data_processing_update(
        self, 
        user_id: str, 
        data_source_id: str, 
        status: str, 
        progress: int = 0, 
        message: str = "", 
        details: Dict[str, Any] = None
    ):
        """Send data processing status update"""
        update_message = {
            "type": "data_processing_update",
            "data_source_id": data_source_id,
            "status": status,
            "progress": progress,
            "message": message,
            "details": details or {},
            "timestamp": self._get_timestamp()
        }
        
        await self.send_to_user(user_id, update_message)
        logger.info(f"Sent processing update: {status} ({progress}%) - {message}")
    
    async def send_query_update(
        self, 
        user_id: str, 
        query_id: str, 
        status: str, 
        progress: int = 0, 
        message: str = "", 
        results: Dict[str, Any] = None
    ):
        """Send query processing status update"""
        update_message = {
            "type": "query_update",
            "query_id": query_id,
            "status": status,
            "progress": progress,
            "message": message,
            "results": results,
            "timestamp": self._get_timestamp()
        }
        
        await self.send_to_user(user_id, update_message)
        logger.info(f"Sent query update: {status} ({progress}%) - {message}")
    
    async def send_error(self, user_id: str, error_type: str, message: str, details: Dict[str, Any] = None):
        """Send error message"""
        error_message = {
            "type": "error",
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "timestamp": self._get_timestamp()
        }
        
        await self.send_to_user(user_id, error_message)
        logger.error(f"Sent error to user {user_id}: {error_type} - {message}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        import datetime
        return datetime.datetime.utcnow().isoformat()
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get number of users with active connections"""
        return len(self.user_sessions)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()