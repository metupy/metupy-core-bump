# metupy/studio/routes/page_routes.py
"""Page Management Routes."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
from metupy import studio
from metupy.models.page import PageModel

def setup(app: web.Application, studio):
    """Setup page routes."""
    app.router.add_get('/dashboard/pages', pages_list)
    app.router.add_get('/dashboard/pages/new', new_page)
    app.router.add_post('/dashboard/pages', create_page)
    app.router.add_get('/dashboard/pages/{page_id}', edit_page)
    app.router.add_post('/dashboard/pages/{page_id}', update_page)
    app.router.add_delete('/dashboard/pages/{page_id}', delete_page)
    app.router.add_post('/dashboard/pages/{page_id}/publish', publish_page)

async def pages_list(request: web.Request):
    """List all pages."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    pages = PageModel.select().order_by(PageModel.order)
    
    context = {
        'title': 'Pages',
        'active_page': 'pages',
        'pages': [page.to_dict() for page in pages],
    }
    return render_template('dashboard/pages/list.html', request, context)

async def new_page(request: web.Request):
    """New page form."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    context = {
        'title': 'New Page',
        'active_page': 'pages',
        'templates': await get_available_templates(),
    }
    return render_template('dashboard/pages/new.html', request, context)

async def create_page(request: web.Request):
    """Create new page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    # Validate
    if not data.get('title'):
        return web.json_response({
            'success': False,
            'error': 'Title is required'
        }, status=400)
        
    # Generate slug
    from metupy.utils.helpers import slugify
    slug = data.get('slug') or slugify(data['title'])
    
    # Check slug availability
    if PageModel.select().where(PageModel.slug == slug).exists():
        return web.json_response({
            'success': False,
            'error': 'Slug already exists'
        }, status=400)
        
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
    )
    
    return web.json_response({
        'success': True,
        'page': page.to_dict(),
        'redirect': f'/dashboard/pages/{page.id}'
    })

async def edit_page(request: web.Request):
    """Edit page form."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    page_id = request.match_info['page_id']  # Now UUID string
    
    try:
        # Convert string to UUID
        from uuid import UUID
        page_uuid = UUID(page_id)
        page = PageModel.get_by_id(page_uuid)
    except (ValueError, PageModel.DoesNotExist):
        return web.Response(text='Page not found', status=404)
        
    context = {
        'title': f'Edit: {page.title}',
        'active_page': 'pages',
        'page': page.to_dict(),
        'templates': await get_available_templates(),
    }
    return render_template('dashboard/pages/edit.html', request, context)

async def update_page(request: web.Request):
    """Update page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = int(request.match_info['page_id'])
    data = await request.json()
    
    try:
        page = PageModel.get_by_id(page_id)
    except PageModel.DoesNotExist:
        return web.json_response({'error': 'Page not found'}, status=404)
        
    # Update fields
    for field in ['title', 'content', 'template', 'status', 'order', 'meta_description', 'meta_keywords']:
        if field in data:
            setattr(page, field, data[field])
            
    page.save()
    
    return web.json_response({
        'success': True,
        'page': page.to_dict()
    })

async def delete_page(request: web.Request):
    """Delete page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = int(request.match_info['page_id'])
    
    try:
        page = PageModel.get_by_id(page_id)
        page.delete_instance()
        return web.json_response({'success': True})
    except PageModel.DoesNotExist:
        return web.json_response({'error': 'Page not found'}, status=404)

async def publish_page(request: web.Request):
    """Publish page."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    page_id = int(request.match_info['page_id'])
    
    try:
        page = PageModel.get_by_id(page_id)
        page.status = 'published'
        page.save()
        return web.json_response({'success': True})
    except PageModel.DoesNotExist:
        return web.json_response({'error': 'Page not found'}, status=404)

async def get_available_templates():
    """Get available templates."""
    templates = []
    
    # Get theme templates
    if studio.engine.theme_manager.active_theme:
        templates_dir = studio.engine.theme_manager.active_theme.path / 'templates'
        if templates_dir.exists():
            templates.extend([
                {'name': t.name, 'path': str(t.relative_to(templates_dir))}
                for t in templates_dir.glob('*.html')
            ])
            
    return templates