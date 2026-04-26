from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.live_stream_manager import LiveStreamManager
import logging

logger = logging.getLogger("WebRTCRouter")
router = APIRouter()

@router.websocket("/ws/interview/{session_id}")
async def websocket_interview_endpoint(websocket: WebSocket, session_id: str):
    """
    Handles bidirectional streaming for live interviews.
    """
    await websocket.accept()
    manager = LiveStreamManager(session_id)
    await manager.connect()

    try:
        while True:
            # Receive text, audio, or video blobs from the client
            message = await websocket.receive_bytes()
            
            # Simple routing based on a theoretical header or frame marker
            # For this scaffolding, we treat it as an audio chunk
            await manager.process_audio_chunk(message)
            
            # In a real implementation, a background task would be consuming 
            # manager.output_stream() and sending it back via websocket.send_bytes()
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from live session {session_id}")
        await manager.disconnect()
    except Exception as e:
        logger.error(f"Error in websocket stream: {e}")
        await manager.disconnect()
