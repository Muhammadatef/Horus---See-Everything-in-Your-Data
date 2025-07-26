"""
WebSocket endpoints for real-time communication
"""

import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str = Query(default="default"),
    connection_id: str = Query(default=None)
):
    """WebSocket endpoint for real-time updates"""
    
    # Generate connection ID if not provided
    if not connection_id:
        connection_id = str(uuid.uuid4())
    
    # Connect to WebSocket manager
    await websocket_manager.connect(websocket, connection_id, user_id)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client (heartbeat, etc.)
                message = await websocket.receive_text()
                logger.debug(f"Received WebSocket message from {connection_id}: {message}")
                
                # Handle specific message types if needed
                # For now, just acknowledge receipt
                await websocket_manager.send_to_connection(connection_id, {
                    "type": "message_received",
                    "original_message": message,
                    "timestamp": websocket_manager._get_timestamp()
                })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {connection_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket communication with {connection_id}: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {connection_id} disconnected")
    
    finally:
        # Clean up connection
        websocket_manager.disconnect(connection_id, user_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "active_users": websocket_manager.get_user_count(),
        "status": "operational"
    }