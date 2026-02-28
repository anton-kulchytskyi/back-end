"""WebSocket service for real-time notification handling."""

from fastapi import WebSocket, WebSocketDisconnect, status

from app.core.logger import logger
from app.core.websocket_manager import WebSocketManager
from app.models.user.user import User


class WebSocketService:
    """
    Service for handling WebSocket connections and messaging.

    Responsibilities:
    - Manage connection lifecycle (connect, disconnect)
    - Handle incoming messages (ping, etc.)
    - Send outgoing messages (notifications, pongs, etc.)
    - Error handling
    """

    def __init__(self, manager: WebSocketManager):
        """
        Initialize WebSocketService.

        Args:
            manager: WebSocketManager instance (injected dependency)
        """
        self.manager = manager

    async def handle_connection(
        self,
        websocket: WebSocket,
        user: User,
    ) -> None:
        """
        Handle WebSocket connection lifecycle.

        This is the main entry point for WebSocket endpoints.
        Manages the entire connection from connect to disconnect.

        Args:
            websocket: WebSocket connection instance
            user: Authenticated user
        """
        try:
            # 1. Connect user
            await self._connect_user(websocket, user)

            # 2. Send connection confirmation
            await self._send_connected_message(websocket, user)

            # 3. Keep connection alive and handle messages
            await self._message_loop(websocket, user)

        except WebSocketDisconnect:
            # Normal disconnect
            logger.info(f"User {user.id} disconnected from WebSocket")
            self._disconnect_user(user, websocket)

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected WebSocket error for user {user.id}: {e}")
            self._disconnect_user(user, websocket)

            # Try to close connection gracefully
            if websocket.client_state.value in [0, 1]:  # CONNECTING or CONNECTED
                try:
                    await websocket.close(
                        code=status.WS_1011_INTERNAL_ERROR,
                        reason="Internal server error",
                    )
                except Exception:
                    pass

    async def _connect_user(self, websocket: WebSocket, user: User) -> None:
        """Accept WebSocket connection and register user."""
        await self.manager.connect(user.id, websocket)
        logger.info(
            f"WebSocket connected: user_id={user.id}, "
            f"active_connections={self.manager.get_connection_count(user.id)}"
        )

    def _disconnect_user(self, user: User, websocket: WebSocket) -> None:
        """Disconnect user and cleanup."""
        self.manager.disconnect(user.id, websocket)
        logger.info(
            f"WebSocket disconnected: user_id={user.id}, "
            f"remaining_connections={self.manager.get_connection_count(user.id)}"
        )

    async def _send_connected_message(
        self,
        websocket: WebSocket,
        user: User,
    ) -> None:
        """Send connection confirmation to client."""
        await websocket.send_json(
            {
                "type": "connected",
                "data": {
                    "message": "Successfully connected to notifications",
                    "user_id": user.id,
                },
            }
        )

    async def _message_loop(self, websocket: WebSocket, user: User) -> None:
        """
        Keep connection alive and handle incoming messages.

        Raises:
            WebSocketDisconnect: When client disconnects
        """
        while True:
            # Wait for message from client
            data = await websocket.receive_json()

            # Handle message
            await self._handle_client_message(websocket, user, data)

    async def _handle_client_message(
        self,
        websocket: WebSocket,
        user: User,
        data: dict,
    ) -> None:
        """
        Handle incoming message from client.

        Args:
            websocket: WebSocket connection
            user: Authenticated user
            data: Message data from client
        """
        message_type = data.get("type")

        if message_type == "ping":
            await self._handle_ping(websocket, user)
        else:
            logger.warning(f"Unknown message type from user {user.id}: {message_type}")

    async def _handle_ping(self, websocket: WebSocket, user: User) -> None:
        """
        Handle ping message from client.

        Responds with pong to keep connection alive.
        """
        await websocket.send_json(
            {"type": "pong", "data": {"message": "Connection alive"}}
        )
        logger.debug(f"Ping/pong: user_id={user.id}")

    async def send_notification_to_user(
        self,
        user_id: int,
        notification_data: dict,
    ) -> int:
        """
        Send notification to specific user via WebSocket.

        Args:
            user_id: ID of user to send notification to
            notification_data: Notification data to send

        Returns:
            Number of successful sends (number of user's active connections)
        """
        message = {
            "type": "new_notification",
            "data": notification_data,
        }

        sent_count = await self.manager.send_personal(user_id, message)

        logger.debug(
            f"Notification sent via WebSocket: user_id={user_id}, "
            f"connections_reached={sent_count}"
        )

        return sent_count

    async def broadcast_all_notifications_read(self, user_id: int) -> int:
        """
        Notify user's other devices that all notifications were marked as read.
        """
        message = {
            "type": "all_notifications_read",
            "data": {},
        }

        sent_count = await self.manager.send_personal(user_id, message)

        logger.debug(
            f"All-notifications-read broadcast: user_id={user_id}, "
            f"connections_reached={sent_count}"
        )

        return sent_count

    async def broadcast_notification_read(
        self,
        user_id: int,
        notification_id: int,
    ) -> int:
        """
        Broadcast notification read status to user's other devices.

        When user marks notification as read on one device,
        notify their other connected devices.

        Args:
            user_id: ID of user
            notification_id: ID of notification that was marked as read

        Returns:
            Number of successful broadcasts
        """
        message = {
            "type": "notification_read",
            "data": {
                "id": notification_id,
                "status": "read",
            },
        }

        sent_count = await self.manager.send_personal(user_id, message)

        logger.debug(
            f"Notification read broadcast: user_id={user_id}, "
            f"notification_id={notification_id}, "
            f"connections_reached={sent_count}"
        )

        return sent_count
