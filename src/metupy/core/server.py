# metupy/core/server.py
"""Aiohttp web server untuk Metupy."""

from aiohttp import web
from aiohttp_jinja2 import setup as setup_jinja2
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import jinja2
from pathlib import Path
import asyncio
import hashlib

class MetupyServer:
    """Web server untuk Metupy."""
    
    def __init__(self, engine):
        self.engine = engine
        self.app = web.Application()
        self.setup_middleware()
        self.setup_templates()
        self.setup_routes()
        self.setup_static()
        
    def setup_middleware(self):
        """Setup middleware."""
        # Session middleware
        secret_key = self.engine.config.SECRET_KEY
        self.app.middlewares.append(
            session_middleware(
                EncryptedCookieStorage(secret_key.encode())
            )
        )
        
    def setup_templates(self):
        """Setup template engine."""
        template_dirs = [
            self.engine.theme_dir / 'templates',
            self.engine.content_dir / 'templates',
            Path(__file__).parent.parent / 'templates',
        ]
        
        setup_jinja2(
            self.app,
            loader=jinja2.FileSystemLoader([
                str(d) for d in template_dirs if d.exists()
            ])
        )
        
    def setup_routes(self):
        """Setup routes."""
        # Main routes
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/{path:.*}', self.serve_content)
        
        # API routes
        self.app.router.add_get('/api/site', self.api_site_info)
        self.app.router.add_get('/api/search', self.api_search)
        
        # Plugin routes
        self.engine.plugin_manager.setup_routes(self.app)
        
    def setup_static(self):
        """Setup static files."""
        # Output directory
        self.app.router.add_static(
            '/',
            path=str(self.engine.output_dir),
            name='output'
        )
        
        # Assets
        if self.engine.assets_dir.exists():
            self.app.router.add_static(
                '/assets/',
                path=str(self.engine.assets_dir),
                name='assets'
            )
            
        # Theme static
        theme_static = self.engine.theme_dir / 'static'
        if theme_static.exists():
            self.app.router.add_static(
                '/theme/',
                path=str(theme_static),
                name='theme'
            )
            
    async def index(self, request):
        """Index route."""
        index_file = self.engine.output_dir / 'index.html'
        if index_file.exists():
            return web.FileResponse(index_file)
        return web.Response(text="Metupy Server Running", content_type='text/html')
        
    async def serve_content(self, request):
        """Serve content files."""
        path = request.match_info['path']
        
        # Check output directory
        file_path = self.engine.output_dir / path
        if file_path.exists() and file_path.is_file():
            return web.FileResponse(file_path)
            
        # Check pretty URLs
        if self.engine.config.BUILD_PRETTY_URLS:
            index_path = self.engine.output_dir / path / 'index.html'
            if index_path.exists():
                return web.FileResponse(index_path)
                
        # 404
        return web.Response(
            text="404 Not Found",
            status=404,
            content_type='text/html'
        )
        
    async def api_site_info(self, request):
        """API: Site information."""
        return web.json_response({
            'name': self.engine.config.SITE_NAME,
            'version': self.engine.config.SITE_VERSION,
            'description': self.engine.config.SITE_DESCRIPTION,
            'url': self.engine.config.SITE_URL,
        })
        
    async def api_search(self, request):
        """API: Search content."""
        query = request.query.get('q', '')
        results = self.engine.content_manager.search_content(query)
        return web.json_response({
            'query': query,
            'results': results,
        })
        
    async def start(self):
        """Start server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            self.engine.config.DEV_HOST,
            self.engine.config.DEV_PORT
        )
        await site.start()
        
        print(f"Server running at http://{self.engine.config.DEV_HOST}:{self.engine.config.DEV_PORT}")
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()