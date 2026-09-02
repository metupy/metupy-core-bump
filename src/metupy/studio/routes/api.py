# metupy/studio/routes/api_routes.py
"""API Routes untuk Metupy Studio."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
from websockets import asyncio
from metupy import studio
from metupy.models.page import PageModel
from metupy.models.plugin import PluginModel
from metupy.models.theme import ThemeModel
from metupy.models.widget import WidgetModel
from metupy.models.comment import CommentModel
from metupy.models.user import User
from metupy.models.activity import ActivityLogModel
import json
import uuid
from datetime import datetime

def setup(app: web.Application, studio):
    """Setup API routes."""
    # Pages API
    app.router.add_get('/api/pages', api_get_pages)
    app.router.add_get('/api/pages/{page_id}', api_get_page)
    app.router.add_post('/api/pages', api_create_page)
    app.router.add_put('/api/pages/{page_id}', api_update_page)
    app.router.add_delete('/api/pages/{page_id}', api_delete_page)
    app.router.add_post('/api/pages/{page_id}/publish', api_publish_page)
    app.router.add_post('/api/pages/{page_id}/unpublish', api_unpublish_page)
    
    # Plugins API
    app.router.add_get('/api/plugins', api_get_plugins)
    app.router.add_get('/api/plugins/{plugin_id}', api_get_plugin) # type: ignore
    app.router.add_post('/api/plugins', api_create_plugin) # type: ignore
    app.router.add_put('/api/plugins/{plugin_id}', api_update_plugin) # type: ignore
    app.router.add_delete('/api/plugins/{plugin_id}', api_delete_plugin) # type: ignore
    app.router.add_post('/api/plugins/{plugin_id}/activate', api_activate_plugin)
    app.router.add_post('/api/plugins/{plugin_id}/deactivate', api_deactivate_plugin)
    
    # Themes API
    app.router.add_get('/api/themes', api_get_themes) # type: ignore
    app.router.add_get('/api/themes/{theme_id}', api_get_theme) # type: ignore
    app.router.add_post('/api/themes/{theme_id}/activate', api_activate_theme) # type: ignore
    
    # Widgets API
    app.router.add_get('/api/widgets', api_get_widgets) # type: ignore
    app.router.add_get('/api/widgets/{widget_id}', api_get_widget) # type: ignore
    app.router.add_post('/api/widgets', api_create_widget) # type: ignore
    app.router.add_put('/api/widgets/{widget_id}', api_update_widget) # type: ignore
    app.router.add_delete('/api/widgets/{widget_id}', api_delete_widget) # type: ignore
    
    # Comments API
    app.router.add_get('/api/comments', api_get_comments) # type: ignore
    app.router.add_get('/api/comments/{comment_id}', api_get_comment) # type: ignore
    app.router.add_put('/api/comments/{comment_id}', api_update_comment) # type: ignore
    app.router.add_delete('/api/comments/{comment_id}', api_delete_comment) # type: ignore
    app.router.add_post('/api/comments/{comment_id}/approve', api_approve_comment) # type: ignore
    app.router.add_post('/api/comments/{comment_id}/spam', api_mark_comment_spam) # type: ignore
    
    # Users API
    app.router.add_get('/api/users', api_get_users) # type: ignore
    app.router.add_get('/api/users/{user_id}', api_get_user) # type: ignore
    app.router.add_put('/api/users/{user_id}', api_update_user) # type: ignore
    app.router.add_delete('/api/users/{user_id}', api_delete_user) # type: ignore
    
    # Activity API
    app.router.add_get('/api/activity', api_get_activity) # type: ignore
    
    # Search API
    app.router.add_get('/api/search', api_search)
    
    # Stats API
    app.router.add_get('/api/stats', api_get_stats)
    
    # Build API
    app.router.add_post('/api/build', api_trigger_build)
    
    # Export/Import API
    app.router.add_get('/api/export', api_export_data) # type: ignore
    app.router.add_post('/api/import', api_import_data) # type: ignore

# ═══ Pages API ═══

async def api_get_pages(request: web.Request):
    """Get all pages."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    # Query parameters
    page = int(request.query.get('page', 1))
    per_page = int(request.query.get('per_page', 10))
    status = request.query.get('status')
    search = request.query.get('search')
    
    # Build query
    query = PageModel.select()
    
    if status:
        query = query.where(PageModel.status == status)
        
    if search:
        query = query.where(
            (PageModel.title.contains(search)) |
            (PageModel.content.contains(search))
        )
        
    # Get total count
    total = query.count()
    
    # Paginate
    pages = query.order_by(PageModel.order).paginate(page, per_page)
    
    return web.json_response({
        'success': True,
        'data': [p.to_dict() for p in pages],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page,
        }
    })

async def api_get_page(request: web.Request):
    """Get single page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = request.match_info['page_id']
    
    try:
        page_uuid = uuid.UUID(page_id)
        page = PageModel.get_by_id(page_uuid)
        return web.json_response({
            'success': True,
            'data': page.to_dict()
        })
    except (ValueError, PageModel.DoesNotExist):
        return web.json_response({'error': 'Page not found'}, status=404)

async def api_create_page(request: web.Request):
    """Create new page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    # Validate
    if not data.get('title'):
        return web.json_response({'error': 'Title is required'}, status=400)
        
    # Generate slug
    from metupy.utils.helpers import slugify
    slug = data.get('slug') or slugify(data['title'])
    
    # Check slug
    if PageModel.select().where(PageModel.slug == slug).exists():
        return web.json_response({'error': 'Slug already exists'}, status=400)
        
    # Create page
    page = PageModel.create(
        title=data['title'],
        slug=slug,
        content=data.get('content', ''),
        template=data.get('template', 'default.html'),
        status=data.get('status', 'draft'),
        author_id=user_id,
        parent_id=data.get('parent_id'),
        order=data.get('order', 0),
        is_homepage=data.get('is_homepage', False),
        meta_description=data.get('meta_description'),
        meta_keywords=data.get('meta_keywords'),
        content_type=data.get('content_type', 'page'),
        featured_image=data.get('featured_image'),
    )
    
    # Log activity
    ActivityLogModel.create(
        user_id=user_id,
        action='create',
        entity_type='page',
        entity_id=str(page.id),
        description=f'Created page: {page.title}',
    )
    
    return web.json_response({
        'success': True,
        'data': page.to_dict()
    }, status=201)

async def api_update_page(request: web.Request):
    """Update page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = request.match_info['page_id']
    data = await request.json()
    
    try:
        page_uuid = uuid.UUID(page_id)
        page = PageModel.get_by_id(page_uuid)
    except (ValueError, PageModel.DoesNotExist):
        return web.json_response({'error': 'Page not found'}, status=404)
        
    # Update fields
    updatable_fields = [
        'title', 'content', 'template', 'status', 'order',
        'meta_description', 'meta_keywords', 'content_type',
        'featured_image', 'parent_id'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(page, field, data[field])
            
    page.save()
    
    # Log activity
    ActivityLogModel.create(
        user_id=user_id,
        action='update',
        entity_type='page',
        entity_id=str(page.id),
        description=f'Updated page: {page.title}',
    )
    
    return web.json_response({
        'success': True,
        'data': page.to_dict()
    })

async def api_delete_page(request: web.Request):
    """Delete page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = request.match_info['page_id']
    
    try:
        page_uuid = uuid.UUID(page_id)
        page = PageModel.get_by_id(page_uuid)
        title = page.title
        page.delete_instance()
        
        # Log activity
        ActivityLogModel.create(
            user_id=user_id,
            action='delete',
            entity_type='page',
            entity_id=page_id,
            description=f'Deleted page: {title}',
        )
        
        return web.json_response({'success': True})
    except (ValueError, PageModel.DoesNotExist):
        return web.json_response({'error': 'Page not found'}, status=404)

async def api_publish_page(request: web.Request):
    """Publish page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = request.match_info['page_id']
    
    try:
        page_uuid = uuid.UUID(page_id)
        page = PageModel.get_by_id(page_uuid)
        page.publish()
        
        # Log activity
        ActivityLogModel.create(
            user_id=user_id,
            action='publish',
            entity_type='page',
            entity_id=str(page.id),
            description=f'Published page: {page.title}',
        )
        
        return web.json_response({'success': True})
    except (ValueError, PageModel.DoesNotExist):
        return web.json_response({'error': 'Page not found'}, status=404)

async def api_unpublish_page(request: web.Request):
    """Unpublish page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = request.match_info['page_id']
    
    try:
        page_uuid = uuid.UUID(page_id)
        page = PageModel.get_by_id(page_uuid)
        page.unpublish()
        
        return web.json_response({'success': True})
    except (ValueError, PageModel.DoesNotExist):
        return web.json_response({'error': 'Page not found'}, status=404)

# ═══ Plugins API ═══

async def api_get_plugins(request: web.Request):
    """Get all plugins."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugins = PluginModel.select()
    return web.json_response({
        'success': True,
        'data': [p.to_dict() for p in plugins]
    })

async def api_activate_plugin(request: web.Request):
    """Activate plugin."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        plugin.is_active = True
        plugin.save()
        
        # Reload plugin in engine
        await studio.engine.plugin_manager.load_plugins()
        
        return web.json_response({'success': True})
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)

async def api_deactivate_plugin(request: web.Request):
    """Deactivate plugin."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        plugin.is_active = False
        plugin.save()
        
        return web.json_response({'success': True})
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)

# ═══ Search API ═══

async def api_search(request: web.Request):
    """Search content."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    query = request.query.get('q', '')
    search_type = request.query.get('type', 'all')  # all, page, post, comment, user
    
    results = {
        'pages': [],
        'posts': [],
        'comments': [],
        'users': [],
    }
    
    if search_type in ['all', 'page']:
        pages = PageModel.select().where(
            (PageModel.title.contains(query)) |
            (PageModel.content.contains(query))
        ).limit(10)
        results['pages'] = [p.to_dict() for p in pages]
        
    if search_type in ['all', 'comment']:
        comments = CommentModel.select().where(
            CommentModel.content.contains(query)
        ).limit(10)
        results['comments'] = [c.to_dict() for c in comments]
        
    if search_type in ['all', 'user']:
        users = User.select().where(
            (User.username.contains(query)) |
            (User.email.contains(query))
        ).limit(10)
        results['users'] = [u.to_dict() for u in users]
        
    return web.json_response({
        'success': True,
        'query': query,
        'data': results
    })

# ═══ Stats API ═══

async def api_get_stats(request: web.Request):
    """Get stats."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    stats = {
        'pages': {
            'total': PageModel.select().count(),
            'published': PageModel.select().where(PageModel.status == 'published').count(),
            'draft': PageModel.select().where(PageModel.status == 'draft').count(),
        },
        'comments': {
            'total': CommentModel.select().count(),
            'approved': CommentModel.select().where(CommentModel.is_approved == True).count(),
            'pending': CommentModel.select().where(CommentModel.is_approved == False).count(),
            'spam': CommentModel.select().where(CommentModel.is_spam == True).count(),
        },
        'users': {
            'total': User.select().count(),
            'active': User.select().where(User.is_active == True).count(),
        },
        'plugins': {
            'total': PluginModel.select().count(),
            'active': PluginModel.select().where(PluginModel.is_active == True).count(),
        },
        'themes': {
            'total': ThemeModel.select().count(),
            'active': ThemeModel.select().where(ThemeModel.is_active == True).count(),
        },
        'widgets': {
            'total': WidgetModel.select().count(),
            'active': WidgetModel.select().where(WidgetModel.is_active == True).count(),
        },
    }
    
    return web.json_response({
        'success': True,
        'data': stats
    })

# ═══ Build API ═══

async def api_trigger_build(request: web.Request):
    """Trigger site build."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    try:
        # Run build in background
        asyncio.create_task(studio.engine.build())
        
        return web.json_response({
            'success': True,
            'message': 'Build started'
        })
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)