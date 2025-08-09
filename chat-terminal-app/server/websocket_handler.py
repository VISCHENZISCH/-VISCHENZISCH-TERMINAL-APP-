from __future__ import annotations

from typing import Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections and broadcasting.

    Keeps a set of active connections and provides broadcast helpers.
    """

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast_text(self, message: str) -> None:
        stale_connections: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)

    async def broadcast_text_excluding(self, excluded: WebSocket, message: str) -> None:
        stale_connections: list[WebSocket] = []
        for connection in list(self.active_connections):
            if connection is excluded:
                continue
            try:
                await connection.send_text(message)
            except Exception:
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)

    async def send_personal_text(self, websocket: WebSocket, message: str) -> None:
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


