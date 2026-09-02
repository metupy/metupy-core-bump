# metupy/studio/routes/widget_routes.py
"""Widget Routes untuk Studio."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
from metupy import studio
from metupy.models.widget import WidgetModel
from metupy.models.activity import ActivityLogModel
import uuid
import json

def setup(app: web.Application, studio):
    """Setup widget routes."""
    app.router.add_get('/dashboard/widgets', widgets_list)
    app.router.add_get('/dashboard/widgets/new', new_widget)
    app.router.add_post('/dashboard/widgets', create_widget)
    app.router.add_get('/dashboard/widgets/{widget_id}', edit_widget)
    app.router.add_post('/dashboard/widgets/{widget_id}', update_widget)
    app.router.add_delete('/dashboard/widgets/{widget_id}', delete_widget)
    app.router.add_post('/dashboard/widgets/{widget_id}/toggle', toggle_widget)
    app.router.add_post('/dashboard/widgets/reorder', reorder_widgets)

async def widgets_list(request: web.Request):
    """List all widgets."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    widgets = WidgetModel.select().order_by(WidgetModel.area, WidgetModel.order)
    
    context = {
        'title': 'Widgets',
        'active_page': 'widgets',
        'widgets': [w.to_dict() for w in widgets],
        'widget_types': studio.engine.widget_manager.list_widgets(),
    }
    return render_template('dashboard/widgets/list.html', request, context)

async def new_widget(request: web.Request):
    """New widget form."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    context = {
        'title': 'New Widget',
        'active_page': 'widgets',
        'widget_types': studio.engine.widget_manager.list_widgets(),
        'areas': ['sidebar', 'footer', 'header', 'content'],
    }
    return render_template('dashboard/widgets/new.html', request, context)

async def create_widget(request: web.Request):
    """Create new widget."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    # Validate
    if not data.get('name') or not data.get('widget_type'):
        return web.json_response({'error': 'Name and type required'}, status=400)
        
    # Check widget type exists
    widget_type = studio.engine.widget_manager.get_widget(data['widget_type'])
    if not widget_type:
        return web.json_response({'error': 'Invalid widget type'}, status=400)
        
    # Create widget
    widget = WidgetModel.create(
        name=data['name'],
        widget_type=data['widget_type'],
        title=data.get('title'),
        settings=json.dumps(data.get('settings', {})),
        area=data.get('area', 'sidebar'),
        order=data.get('order', 0),
        pages=json.dumps(data.get('pages', [])),
    )
    
    # Log activity
    ActivityLogModel.create(
        user_id=user_id,
        action='create',
        entity_type='widget',
        entity_id=str(widget.id),
        description=f'Created widget: {widget.name}',
    )
    
    return web.json_response({
        'success': True,
        'widget': widget.to_dict(),
    })

async def edit_widget(request: web.Request):
    """Edit widget form."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    widget_id = request.match_info['widget_id']
    
    try:
        widget_uuid = uuid.UUID(widget_id)
        widget = WidgetModel.get_by_id(widget_uuid)
    except (ValueError, WidgetModel.DoesNotExist):
        return web.Response(text='Widget not found', status=404)
        
    context = {
        'title': f'Edit Widget: {widget.name}',
        'active_page': 'widgets',
        'widget': widget.to_dict(),
        'areas': ['sidebar', 'footer', 'header', 'content'],
    }
    return render_template('dashboard/widgets/edit.html', request, context)

async def update_widget(request: web.Request):
    """Update widget."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    widget_id = request.match_info['widget_id']
    data = await request.json()
    
    try:
        widget_uuid = uuid.UUID(widget_id)
        widget = WidgetModel.get_by_id(widget_uuid)
        
        # Update fields
        if 'name' in data:
            widget.name = data['name']
        if 'title' in data:
            widget.title = data['title']
        if 'settings' in data:
            widget.settings = json.dumps(data['settings'])
        if 'area' in data:
            widget.area = data['area']
        if 'order' in data:
            widget.order = data['order']
        if 'pages' in data:
            widget.pages = json.dumps(data['pages'])
            
        widget.save()
        
        return web.json_response({
            'success': True,
            'widget': widget.to_dict(),
        })
    except (ValueError, WidgetModel.DoesNotExist):
        return web.json_response({'error': 'Widget not found'}, status=404)

async def delete_widget(request: web.Request):
    """Delete widget."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    widget_id = request.match_info['widget_id']
    
    try:
        widget_uuid = uuid.UUID(widget_id)
        widget = WidgetModel.get_by_id(widget_uuid)
        name = widget.name
        widget.delete_instance()
        
        # Log activity
        ActivityLogModel.create(
            user_id=user_id,
            action='delete',
            entity_type='widget',
            entity_id=widget_id,
            description=f'Deleted widget: {name}',
        )
        
        return web.json_response({'success': True})
    except (ValueError, WidgetModel.DoesNotExist):
        return web.json_response({'error': 'Widget not found'}, status=404)

async def toggle_widget(request: web.Request):
    """Toggle widget active status."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    widget_id = request.match_info['widget_id']
    
    try:
        widget_uuid = uuid.UUID(widget_id)
        widget = WidgetModel.get_by_id(widget_uuid)
        widget.is_active = not widget.is_active
        widget.save()
        
        return web.json_response({
            'success': True,
            'is_active': widget.is_active,
        })
    except (ValueError, WidgetModel.DoesNotExist):
        return web.json_response({'error': 'Widget not found'}, status=404)

async def reorder_widgets(request: web.Request):
    """Reorder widgets."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    widgets_order = data.get('widgets', [])
    
    for order, widget_id in enumerate(widgets_order):
        try:
            widget_uuid = uuid.UUID(widget_id)
            widget = WidgetModel.get_by_id(widget_uuid)
            widget.order = order
            widget.save()
        except (ValueError, WidgetModel.DoesNotExist):
            pass
            
    return web.json_response({'success': True})