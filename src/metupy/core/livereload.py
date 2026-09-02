# metupy/core/livereload.py
"""Live Reload System."""

import asyncio
import json
import websockets
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Set, Optional
import time

class LiveReloadServer:
    """Live reload server for development."""
    
    def __init__(self, engine):
        self.engine = engine
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.observer = None
        self.event_handler = None
        self.watch_directories = []
        
    async def start(self):
        """Start live reload server."""
        # Setup file watcher
        self._setup_file_watcher()
        
        # Start WebSocket server
        async with websockets.serve(
            self._handle_connection,
            'localhost',
            35729
        ):
            print("🔄 Live reload server started on ws://localhost:35729")
            await asyncio.Future()  # Run forever
            
    def _setup_file_watcher(self):
        """Setup file watcher."""
        self.event_handler = LiveReloadHandler(self)
        self.observer = Observer()
        
        # Watch directories
        watch_patterns = self.engine.config.DEV_WATCH_FILES
        watch_dirs = [
            self.engine.content_dir,
            self.engine.theme_dir,
            self.engine.base_dir / 'pages',
            self.engine.base_dir / 'plugins',
            self.engine.base_dir / 'widgets',
        ]
        
        for directory in watch_dirs:
            if directory.exists():
                self.observer.schedule(self.event_handler, str(directory), recursive=True)
                self.watch_directories.append(directory)
                
        self.observer.start()
        
    async def _handle_connection(self, websocket, path):
        """Handle WebSocket connection."""
        self.clients.add(websocket)
        print(f"🔗 Live reload client connected ({len(self.clients)} clients)")
        
        try:
            # Send initial connection message
            await websocket.send(json.dumps({
                'type': 'connected',
                'message': 'Live reload connected',
            }))
            
            async for message in websocket:
                # Handle client messages
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': time.time(),
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            print(f"🔌 Live reload client disconnected ({len(self.clients)} clients)")
            
    async def reload_page(self, path: str = None):
        """Send reload command to all clients."""
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
        
    async def reload_css(self, path: str = None):
        """Send CSS reload command."""
        if not self.clients:
            return
            
        message = json.dumps({
            'type': 'reload_css',
            'path': path,
            'timestamp': time.time(),
        })
        
        await asyncio.gather(*[
            client.send(message)
            for client in self.clients
        ])
        
    def stop(self):
        """Stop live reload server."""
        if self.observer:
            self.observer.stop()
            self.observer.join()

class LiveReloadHandler(FileSystemEventHandler):
    """File system event handler for live reload."""
    
    def __init__(self, server):
        self.server = server
        self.last_reload = 0
        self.debounce_time = 0.5  # seconds
        
    def on_any_event(self, event):
        """Handle any file system event."""
        # Skip directories
        if event.is_directory:
            return
            
        # Debounce
        current_time = time.time()
        if current_time - self.last_reload < self.debounce_time:
            return
            
        self.last_reload = current_time
        
        # Determine reload type
        if event.src_path.endswith('.css'):
            asyncio.create_task(self.server.reload_css(event.src_path))
        else:
            asyncio.create_task(self.server.reload_page(event.src_path))