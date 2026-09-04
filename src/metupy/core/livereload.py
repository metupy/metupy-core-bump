"""
Live reload server for Metupy.

Provides WebSocket-based live reload for development.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional, Set

import websockets
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class LiveReloadServer:
    """Live reload server using WebSocket."""

    def __init__(self, engine):
        """
        Initialize LiveReloadServer.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.clients: Set = set()
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[FileSystemEventHandler] = None
        self.port = 35729

    async def start(self) -> None:
        """Start live reload server."""
        self._setup_file_watcher()

        async with websockets.serve(
            self._handle_connection,
            'localhost',
            self.port
        ):
            print(f"  Live reload server: ws://localhost:{self.port}")
            await asyncio.Future()

    def _setup_file_watcher(self) -> None:
        """Setup file watcher."""
        self.event_handler = LiveReloadHandler(self)
        self.observer = Observer()

        watch_dirs = [
            self.engine.content_dir,
            self.engine.theme_dir,
            self.engine.base_dir / 'pages',
            self.engine.base_dir / 'plugins',
        ]

        for directory in watch_dirs:
            if directory.exists():
                self.observer.schedule(
                    self.event_handler,
                    str(directory),
                    recursive=True
                )

        self.observer.start()

    async def _handle_connection(self, websocket, path):
        """
        Handle WebSocket connection.

        Args:
            websocket: WebSocket connection.
            path: Connection path.
        """
        self.clients.add(websocket)
        print(f"  Live reload client connected ({len(self.clients)} clients)")

        try:
            await websocket.send(json.dumps({
                'type': 'connected',
                'message': 'Live reload connected',
            }))

            async for message in websocket:
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': time.time(),
                    }))

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"  Live reload client disconnected ({len(self.clients)} clients)")

    async def reload_page(self, path: Optional[str] = None) -> None:
        """
        Send reload command to all clients.

        Args:
            path: Optional file path that changed.
        """
        if not self.clients:
            return

        message = json.dumps({
            'type': 'reload',
            'path': path,
            'timestamp': time.time(),
        })

        await asyncio.gather(*[
            client.send(message)
            for client in self.clients
        ])

    def stop(self) -> None:
        """Stop live reload server."""
        if self.observer:
            self.observer.stop()
            self.observer.join()


class LiveReloadHandler(FileSystemEventHandler):
    """File system event handler for live reload."""

    def __init__(self, server: LiveReloadServer):
        """
        Initialize handler.

        Args:
            server: LiveReloadServer instance.
        """
        self.server = server
        self.last_reload = 0
        self.debounce_time = 0.5

    def on_any_event(self, event) -> None:
        """
        Handle file system event.

        Args:
            event: File system event.
        """
        if event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_reload < self.debounce_time:
            return

        self.last_reload = current_time
        asyncio.create_task(self.server.reload_page(event.src_path))