"""
Middleware manager for Metupy.

Provides middleware for authentication, error handling,
security headers, CORS, and logging.
"""

import time
from datetime import datetime
from typing import Any, Callable, List, Optional

from aiohttp import web


class MiddlewareManager:
    """Manage middleware for Metupy."""

    def __init__(self, engine):
        """
        Initialize MiddlewareManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.middlewares: List[Callable] = []
        self.before_request: List[Callable] = []
        self.after_request: List[Callable] = []

    def add_middleware(self, middleware: Callable) -> None:
        """
        Add middleware.

        Args:
            middleware: Middleware callable.
        """
        self.middlewares.append(middleware)

    def setup_default_middleware(self) -> None:
        """Setup default middleware stack."""
        self.add_middleware(self.logging_middleware)
        self.add_middleware(self.error_handler_middleware)
        self.add_middleware(self.security_headers_middleware)
        self.add_middleware(self.cors_middleware)

    async def logging_middleware(self, request: web.Request, handler: Callable):
        """
        Log request and response time.

        Args:
            request: Aiohttp request.
            handler: Next handler.

        Returns:
            Response from handler.
        """
        start_time = time.time()
        print(f"  {request.method} {request.path}")

        try:
            response = await handler(request)
            return response
        finally:
            duration = time.time() - start_time
            print(f"    Completed in {duration:.3f}s")

    async def error_handler_middleware(self, request: web.Request, handler: Callable):
        """
        Handle errors and return JSON for API requests.

        Args:
            request: Aiohttp request.
            handler: Next handler.

        Returns:
            Response from handler or error response.
        """
        try:
            return await handler(request)
        except web.HTTPException as e:
            if request.path.startswith('/api/'):
                return web.json_response(
                    {'error': e.reason, 'status': e.status},
                    status=e.status
                )
            raise
        except Exception as e:
            if request.path.startswith('/api/'):
                return web.json_response(
                    {'error': str(e), 'status': 500},
                    status=500
                )
            raise

    async def security_headers_middleware(self, request: web.Request, handler: Callable):
        """
        Add security headers to response.

        Args:
            request: Aiohttp request.
            handler: Next handler.

        Returns:
            Response with security headers.
        """
        response = await handler(request)

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    async def cors_middleware(self, request: web.Request, handler: Callable):
        """
        Add CORS headers to response.

        Args:
            request: Aiohttp request.
            handler: Next handler.

        Returns:
            Response with CORS headers.
        """
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)

        if getattr(self.engine.config, 'CORS_ENABLED', True):
            origins = getattr(self.engine.config, 'CORS_ORIGINS', ['*'])
            if '*' in origins:
                response.headers['Access-Control-Allow-Origin'] = '*'
            else:
                origin = request.headers.get('Origin', '')
                if origin in origins:
                    response.headers['Access-Control-Allow-Origin'] = origin

            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        return response