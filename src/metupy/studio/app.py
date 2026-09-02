# metupy/studio/app.py
from aiohttp import web
import asyncio
import webbrowser
from pathlib import Path
from metupy.core.security import SecurityManager
from metupy.studio.routes import setup_routes, dashboard_routes, auth_routes
from metupy.models.user import User
from metupy.models.page import PageModel

class StudioApp:
    """Metupy Studio Application"""
    
    def __init__(self, engine):
        self.engine = engine
        self.app = web.Application()
        self.security = SecurityManager(engine.config.SECRET_KEY)
        self.setup_database()
        self.setup_routes()
        self.setup_middleware()
        
def setup_database(self):
    """Setup database connection."""
    from metupy.models.base import init_database
    from metupy.models.user import User
    from metupy.models.page import PageModel
    from metupy.models.plugin import PluginModel
    from metupy.models.theme import ThemeModel
    from metupy.models.widget import WidgetModel
    from metupy.models.comment import CommentModel
    from metupy.models.session import SessionModel
    from metupy.models.activity import ActivityLogModel
    
    self.db = init_database(self.engine.config)
    self.db.connect()
    
    # Create all tables
    self.db.create_tables([
        User,
        PageModel,
        PluginModel,
        ThemeModel,
        WidgetModel,
        CommentModel,
        SessionModel,
        ActivityLogModel,
    ]) 
    def setup_routes(self):
        """Setup studio routes"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/setup', setup_routes.setup_wizard)
        self.app.router.add_post('/setup', setup_routes.process_setup)
        self.app.router.add_get('/login', auth_routes.login_page)
        self.app.router.add_post('/login', auth_routes.login)
        self.app.router.add_get('/logout', auth_routes.logout)
        self.app.router.add_get('/dashboard', dashboard_routes.index)
        self.app.router.add_get('/dashboard/pages', dashboard_routes.pages)
        self.app.router.add_get('/dashboard/pages/new', dashboard_routes.new_page)
        self.app.router.add_post('/dashboard/pages', dashboard_routes.create_page)
        self.app.router.add_get('/dashboard/themes', dashboard_routes.themes)
        self.app.router.add_get('/dashboard/plugins', dashboard_routes.plugins)
        self.app.router.add_get('/dashboard/widgets', dashboard_routes.widgets)
        self.app.router.add_get('/dashboard/settings', dashboard_routes.settings)
        
    def setup_middleware(self):
        """Setup middleware"""
        from metupy.studio.middleware import AuthMiddleware
        self.app.middlewares.append(AuthMiddleware(self.security))
        
    async def start(self):
        """Start studio server"""
        port = self.engine.config.STUDIO_PORT
        
        # Auto open browser
        if self.engine.config.STUDIO['auto_open_browser']:
            asyncio.get_event_loop().call_later(
                1, 
                lambda: webbrowser.open(f'http://localhost:{port}')
            )
            
        # Start server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()
        
        print(f"Metupy Studio running at http://localhost:{port}")
        
    async def index(self, request):
        """Index route"""
        if self.engine.config.STUDIO['setup_required']:
            # Check if setup is complete
            if not self.is_setup_complete():
                raise web.HTTPFound('/setup')
            else:
                raise web.HTTPFound('/login')
        else:
            raise web.HTTPFound('/dashboard')
            
    def is_setup_complete(self):
        """Check if setup is complete"""
        # Check for setup flag in database
        return False