"""WebSocket endpoint for real-time notifications."""

from fastapi import APIRouter, Depends, WebSocket

from app.core.dependencies import get_current_user_websocket, get_websocket_service
from app.models.user.user import User
from app.services.notification.websocket_service import WebSocketService

router = APIRouter(tags=["WebSocket"])


@router.websocket("/websocket/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_websocket),
    websocket_service: WebSocketService = Depends(get_websocket_service),
) -> None:
    """
    WebSocket endpoint for real-time notifications.

    Authentication:
        ws://host/websocket/notifications?token=YOUR_JWT_TOKEN

    Message Types (Server → Client):
        - new_notification: New notification received
        - notification_read: Notification marked as read
        - connected: Connection established
        - pong: Response to ping

    Message Types (Client → Server):
        - ping: Keep-alive heartbeat

    See WebSocketService for detailed message format documentation.
    """
    # Delegate все до service
    await websocket_service.handle_connection(websocket, current_user)
