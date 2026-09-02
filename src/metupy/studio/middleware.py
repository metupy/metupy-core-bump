# metupy/studio/middleware.py
"""Studio Middleware."""

from aiohttp import web
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
import time
import json

class AuthMiddleware:
    """Authentication middleware."""
    
    def __init__(self, security):
        self.security = security
        
    async def __call__(self, request, handler):
        """Process request."""
        # Skip auth for public routes
        public_routes = ['/', '/login', '/register', '/forgot-password', '/reset-password', '/setup']
        
        if request.path in public_routes or request.path.startswith('/static/'):
            return await handler(request)
            
        # Check authentication
        user_id = await authorized_userid(request)
        if not user_id:
            if request.path.startswith('/api/'):
                return web.json_response({'error': 'Unauthorized'}, status=401)
            raise web.HTTPFound('/login')
            
        # Add user to request
        request['user_id'] = user_id
        
        return await handler(request)

class ErrorMiddleware:
    """Error handling middleware."""
    
    async def __call__(self, request, handler):
        """Process request."""
        try:
            return await handler(request)
        except web.HTTPException as e:
            if request.path.startswith('/api/'):
                return web.json_response({
                    'error': e.reason,
                    'status': e.status,
                }, status=e.status)
            raise
        except Exception as e:
            if request.path.startswith('/api/'):
                return web.json_response({
                    'error': str(e),
                    'status': 500,
                }, status=500)
            raise

class LoggingMiddleware:
    """Logging middleware."""
    
    async def __call__(self, request, handler):
        """Process request."""
        start_time = time.time()
        
        try:
            response = await handler(request)
            return response
        finally:
            duration = time.time() - start_time
            print(f"{request.method} {request.path} - {duration:.3f}s")