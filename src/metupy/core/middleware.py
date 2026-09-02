# metupy/core/middleware.py
"""Middleware Manager untuk Metupy."""

from aiohttp import web
from typing import Callable, List, Dict, Any, Optional
import time
import json
from datetime import datetime

class MiddlewareManager:
    """Manages middleware for Metupy."""
    
    def __init__(self, engine):
        self.engine = engine
        self.middlewares: List[Callable] = []
        self.before_request: List[Callable] = []
        self.after_request: List[Callable] = []
        
    def add_middleware(self, middleware: Callable):
        """Add middleware."""
        self.middlewares.append(middleware)
        
    def add_before_request(self, handler: Callable):
        """Add before request handler."""
        self.before_request.append(handler)
        
    def add_after_request(self, handler: Callable):
        """Add after request handler."""
        self.after_request.append(handler)
        
    async def process_request(self, request: web.Request) -> Optional[web.Response]:
        """Process request through middleware."""
        # Execute before request handlers
        for handler in self.before_request:
            result = await handler(request)
            if result:
                return result
                
        return None
        
    async def process_response(self, request: web.Request, response: web.Response) -> web.Response:
        """Process response through middleware."""
        # Execute after request handlers
        for handler in self.after_request:
            response = await handler(request, response)
            
        return response
        
    def setup_default_middleware(self):
        """Setup default middleware."""
        self.add_middleware(self.logging_middleware)
        self.add_middleware(self.error_handler_middleware)
        self.add_middleware(self.security_headers_middleware)
        self.add_middleware(self.cors_middleware)
        self.add_middleware(self.compression_middleware)
        
    async def logging_middleware(self, request: web.Request, handler: Callable):
        """Logging middleware."""
        start_time = time.time()
        
        # Log request
        print(f"{datetime.now().isoformat()} - {request.method} {request.path}")
        
        try:
            response = await handler(request)
            return response
        finally:
            duration = time.time() - start_time
            print(f"  Completed in {duration:.3f}s")
            
    async def error_handler_middleware(self, request: web.Request, handler: Callable):
        """Error handling middleware."""
        try:
            return await handler(request)
        except web.HTTPException as e:
            if request.path.startswith('/api/'):
                return web.json_response({
                    'success': False,
                    'error': e.reason,
                    'status': e.status,
                }, status=e.status)
            raise
        except Exception as e:
            if request.path.startswith('/api/'):
                return web.json_response({
                    'success': False,
                    'error': str(e),
                    'status': 500,
                }, status=500)
            raise
            
    async def security_headers_middleware(self, request: web.Request, handler: Callable):
        """Add security headers."""
        response = await handler(request)
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
        
    async def cors_middleware(self, request: web.Request, handler: Callable):
        """CORS middleware."""
        # Handle OPTIONS request
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)
            
        # Add CORS headers
        if self.engine.config.CORS_ENABLED:
            origins = self.engine.config.CORS_ORIGINS
            if '*' in origins:
                response.headers['Access-Control-Allow-Origin'] = '*'
            else:
                origin = request.headers.get('Origin', '')
                if origin in origins:
                    response.headers['Access-Control-Allow-Origin'] = origin
                    
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
        return response
        
    async def compression_middleware(self, request: web.Request, handler: Callable):
        """Compression middleware."""
        response = await handler(request)
        
        # Check if response should be compressed
        if response.content_type in ['text/html', 'text/css', 'application/javascript']:
            if len(response.body) > 1024:  # Only compress if > 1KB
                import gzip
                import io
                
                compressed = io.BytesIO()
                with gzip.GzipFile(fileobj=compressed, mode='wb') as f:
                    f.write(response.body)
                    
                response.body = compressed.getvalue()
                response.headers['Content-Encoding'] = 'gzip'
                
        return response