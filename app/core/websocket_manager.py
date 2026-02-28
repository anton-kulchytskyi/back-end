"""WebSocket connection manager for real-time notifications."""

from typing import Dict, Set

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.logger import logger


class WebSocketManager:
    """
    Manages WebSocket connections for users.

    Stores multiple connections per user (e.g., multiple devices/tabs).
    """

    def __init__(self) -> None:
        # user_id → set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Accept WebSocket connection and add to active connections.
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        logger.info(
            "WebSocket connected: user_id=%s, total_connections=%s",
            user_id,
            len(self.active_connections[user_id]),
        )

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection from active connections.
        """
        connections = self.active_connections.get(user_id)

        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            del self.active_connections[user_id]

        logger.info(
            "WebSocket disconnected: user_id=%s, remaining_connections=%s",
            user_id,
            len(self.active_connections.get(user_id, set())),
        )

    async def send_personal(self, user_id: int, message: dict) -> int:
        """
        Send message to all active connections of a specific user.
        """
        connections = self.active_connections.get(user_id)

        if not connections:
            logger.debug("No active WebSocket connections for user_id=%s", user_id)
            return 0

        sent_count = 0
        dead_connections: list[WebSocket] = []

        # IMPORTANT: iterate over a copy
        for connection in list(connections):
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                    sent_count += 1
                else:
                    dead_connections.append(connection)
            except Exception as e:
                logger.warning(
                    "WebSocket send failed: user_id=%s, error=%s",
                    user_id,
                    e,
                )
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(user_id, connection)

        logger.debug(
            "WebSocket send_personal: user_id=%s, sent=%s, removed=%s",
            user_id,
            sent_count,
            len(dead_connections),
        )

        return sent_count

    async def broadcast(self, message: dict) -> int:
        """
        Broadcast message to all connected users.
        """
        total_sent = 0

        for user_id in list(self.active_connections.keys()):
            total_sent += await self.send_personal(user_id, message)

        logger.info("WebSocket broadcast sent to %s connections", total_sent)

        return total_sent

    def get_connection_count(self, user_id: int) -> int:
        """
        Get number of active connections for a user.
        """
        return len(self.active_connections.get(user_id, set()))

    def get_total_connections(self) -> int:
        """
        Get total number of active connections.
        """
        return sum(len(conns) for conns in self.active_connections.values())

    def get_connected_users(self) -> list[int]:
        """
        Get list of connected user IDs.
        """
        return list(self.active_connections.keys())


# Global instance (managed by dependency)
_websocket_manager: WebSocketManager | None = None


def get_websocket_manager() -> WebSocketManager:
    """
    Dependency для WebSocketManager.

    Returns singleton instance.
    """
    global _websocket_manager

    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
        logger.info("WebSocketManager initialized")

    return _websocket_manager
