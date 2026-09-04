"""
Web server for Metupy.

Provides aiohttp-based development server for serving
static site output with session support and template rendering.
"""

import asyncio
import signal
from pathlib import Path
from typing import Any, Dict, Optional

import jinja2
from aiohttp import web
from aiohttp_jinja2 import setup as setup_jinja2
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage


class MetupyServer:
    """Development web server for Metupy."""

    def __init__(self, engine):
        """
        Initialize MetupyServer.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.app = web.Application()
        self.setup_middleware()
        self.setup_templates()
        self.setup_routes()
        self.setup_static()

    def setup_middleware(self) -> None:
        """Setup session middleware."""
        secret_key = getattr(self.engine.config, 'SECRET_KEY', 'dev-secret-key')
        self.app.middlewares.append(
            session_middleware(
                EncryptedCookieStorage(secret_key.encode())
            )
        )

    def setup_templates(self) -> None:
        """Setup Jinja2 template engine for server."""
        template_dirs = [
            self.engine.theme_dir / 'templates',
            self.engine.content_dir / 'templates',
            Path(__file__).parent.parent / 'templates',
        ]

        existing_dirs = [str(d) for d in template_dirs if d.exists()]

        setup_jinja2(
            self.app,
            loader=jinja2.FileSystemLoader(existing_dirs) if existing_dirs else None
        )

    def setup_routes(self) -> None:
        """Setup server routes."""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/api/site', self.api_site_info)
        self.app.router.add_get('/api/search', self.api_search)
        self.app.router.add_get('/{path:.*}', self.serve_content)

        plugin_manager = getattr(self.engine, 'plugin_manager', None)
        if plugin_manager:
            try:
                plugin_manager.setup_routes(self.app)
            except Exception as e:
                print(f"  Warning: Plugin routes error: {e}")

    def setup_static(self) -> None:
        """Setup static file serving."""
        if self.engine.output_dir.exists():
            self.app.router.add_static(
                '/',
                path=str(self.engine.output_dir),
                name='output'
            )

        if self.engine.assets_dir.exists():
            self.app.router.add_static(
                '/assets/',
                path=str(self.engine.assets_dir),
                name='assets'
            )

        theme_static = self.engine.theme_dir / 'static'
        if theme_static.exists():
            self.app.router.add_static(
                '/theme/',
                path=str(theme_static),
                name='theme'
            )

    async def index(self, request: web.Request) -> web.Response:
        """
        Serve index page.

        Args:
            request: Aiohttp request.

        Returns:
            File response or text.
        """
        index_file = self.engine.output_dir / 'index.html'
        if index_file.exists():
            return web.FileResponse(index_file)
        return web.Response(text="Metupy Server Running", content_type='text/html')

    async def serve_content(self, request: web.Request) -> web.Response:
        """
        Serve content files from output directory.

        Args:
            request: Aiohttp request.

        Returns:
            File response or 404.
        """
        path = request.match_info['path']
        file_path = self.engine.output_dir / path

        if file_path.exists() and file_path.is_file():
            return web.FileResponse(file_path)

        pretty_urls = getattr(self.engine.config, 'BUILD_PRETTY_URLS', True)
        if pretty_urls:
            index_path = file_path / 'index.html'
            if index_path.exists():
                return web.FileResponse(index_path)

        return web.Response(
            text="404 Not Found",
            status=404,
            content_type='text/html'
        )

    async def api_site_info(self, request: web.Request) -> web.Response:
        """
        Return site information.

        Args:
            request: Aiohttp request.

        Returns:
            JSON response with site info.
        """
        return web.json_response({
            'name': getattr(self.engine.config, 'SITE_NAME', 'Metupy Site'),
            'version': getattr(self.engine.config, 'SITE_VERSION', '1.0.0'),
            'description': getattr(self.engine.config, 'SITE_DESCRIPTION', ''),
            'url': getattr(self.engine.config, 'SITE_URL', 'http://localhost:3155'),
        })

    async def api_search(self, request: web.Request) -> web.Response:
        """
        Search content.

        Args:
            request: Aiohttp request.

        Returns:
            JSON response with search results.
        """
        query = request.query.get('q', '')

        content_manager = getattr(self.engine, 'content_manager', None)
        results = []

        if content_manager and hasattr(content_manager, 'search'):
            results = content_manager.search(query)

        return web.json_response({
            'query': query,
            'results': results,
        })

    async def start(self) -> None:
        """
        Start the server.

        Blocks until Ctrl+C is pressed.
        """
        host = getattr(self.engine.config, 'DEV_HOST', 'localhost')
        port = getattr(self.engine.config, 'DEV_PORT', 3155)

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        print(f"\nServer running at http://{host}:{port}")
        print("Press Ctrl+C to stop\n")

        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()

        def signal_handler() -> None:
            """Handle stop signal."""
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                pass

        try:
            await stop_event.wait()
        finally:
            await runner.cleanup()
            print("Server stopped")