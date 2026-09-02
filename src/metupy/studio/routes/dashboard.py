# metupy/studio/routes/dashboard_routes.py
"""Dashboard Routes."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid

from metupy import studio

def setup(app: web.Application, studio):
    """Setup dashboard routes."""
    app.router.add_get('/dashboard', dashboard_index)
    app.router.add_get('/dashboard/stats', dashboard_stats)
    app.router.add_get('/dashboard/activity', dashboard_activity)

async def dashboard_index(request: web.Request):
    """Dashboard index."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    context = {
        'title': 'Dashboard',
        'active_page': 'dashboard',
        'stats': await get_dashboard_stats(),
    }
    return render_template('dashboard/index.html', request, context)

async def dashboard_stats(request: web.Request):
    """Get dashboard stats."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    stats = await get_dashboard_stats()
    return web.json_response(stats)

async def dashboard_activity(request: web.Request):
    """Get recent activity."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    activity = await get_recent_activity()
    return web.json_response(activity)

async def get_dashboard_stats():
    """Get dashboard statistics."""
    from metupy.models.page import PageModel
    from metupy.models.comment import CommentModel
    from metupy.models.user import User
    
    return {
        'total_pages': PageModel.select().count(),
        'published_pages': PageModel.select().where(PageModel.status == 'published').count(),
        'total_comments': CommentModel.select().count(),
        'pending_comments': CommentModel.select().where(CommentModel.is_approved == False).count(),
        'total_users': User.select().count(),
        'total_plugins': len(studio.engine.plugin_manager.active_plugins),
    }

async def get_recent_activity():
    """Get recent activity."""
    # Implementation for activity log
    return []