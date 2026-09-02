# metupy/studio/routes/plugin_routes.py
"""Plugin Routes untuk Studio."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
from metupy.models.plugin import PluginModel
from metupy.models.activity import ActivityLogModel
import uuid
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

def setup(app: web.Application, studio):
    """Setup plugin routes."""
    app.router.add_get('/dashboard/plugins', plugins_list)
    app.router.add_get('/dashboard/plugins/{plugin_id}', plugin_detail)
    app.router.add_post('/dashboard/plugins/{plugin_id}/activate', activate_plugin)
    app.router.add_post('/dashboard/plugins/{plugin_id}/deactivate', deactivate_plugin)
    app.router.add_delete('/dashboard/plugins/{plugin_id}', delete_plugin)
    app.router.add_post('/dashboard/plugins/upload', upload_plugin)
    app.router.add_get('/dashboard/plugins/{plugin_id}/settings', plugin_settings)
    app.router.add_post('/dashboard/plugins/{plugin_id}/settings', update_plugin_settings)

async def plugins_list(request: web.Request):
    """List all plugins."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    plugins = PluginModel.select()
    
    context = {
        'title': 'Plugins',
        'active_page': 'plugins',
        'plugins': [p.to_dict() for p in plugins],
        'active_plugins': studio.engine.plugin_manager.list_active_plugins(),
    }
    return render_template('dashboard/plugins/list.html', request, context)

async def plugin_detail(request: web.Request):
    """Plugin detail page."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
    except (ValueError, PluginModel.DoesNotExist):
        return web.Response(text='Plugin not found', status=404)
        
    context = {
        'title': f'Plugin: {plugin.name}',
        'active_page': 'plugins',
        'plugin': plugin.to_dict(),
    }
    return render_template('dashboard/plugins/detail.html', request, context)

async def activate_plugin(request: web.Request):
    """Activate plugin."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        
        # Check dependencies
        dependencies = plugin.get_dependencies()
        for dep in dependencies:
            dep_plugin = PluginModel.select().where(PluginModel.name == dep).first()
            if not dep_plugin or not dep_plugin.is_active:
                return web.json_response({
                    'success': False,
                    'error': f'Dependency not met: {dep}'
                }, status=400)
                
        plugin.is_active = True
        plugin.save()
        
        # Reload plugins in engine
        await studio.engine.plugin_manager.load_plugins()
        
        # Log activity
        ActivityLogModel.create(
            user_id=user_id,
            action='activate',
            entity_type='plugin',
            entity_id=str(plugin.id),
            description=f'Activated plugin: {plugin.name}',
        )
        
        return web.json_response({'success': True})
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)

async def deactivate_plugin(request: web.Request):
    """Deactivate plugin."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        
        # Check if other plugins depend on this
        dependent_plugins = PluginModel.select().where(
            PluginModel.dependencies.contains(plugin.name)
        )
        
        for dep_plugin in dependent_plugins:
            if dep_plugin.is_active:
                return web.json_response({
                    'success': False,
                    'error': f'Plugin {dep_plugin.name} depends on this plugin'
                }, status=400)
                
        plugin.is_active = False
        plugin.save()
        
        # Reload plugins
        await studio.engine.plugin_manager.load_plugins()
        
        return web.json_response({'success': True})
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)

async def delete_plugin(request: web.Request):
    """Delete plugin."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        
        # Don't delete active plugin
        if plugin.is_active:
            return web.json_response({'error': 'Cannot delete active plugin'}, status=400)
            
        # Delete plugin directory
        plugin_dir = studio.engine.base_dir / 'plugins' / plugin.name
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)
            
        plugin.delete_instance()
        
        return web.json_response({'success': True})
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)

async def upload_plugin(request: web.Request):
    """Upload plugin."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.post()
    plugin_file = data.get('plugin_file')
    
    if not plugin_file:
        return web.json_response({'error': 'No file uploaded'}, status=400)
        
    # Save uploaded file
    temp_dir = Path(tempfile.mkdtemp())
    zip_path = temp_dir / 'plugin.zip'
    zip_path.write_bytes(plugin_file.file.read())
    
    # Extract zip
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        
    # Find plugin.json
    plugin_json = next(temp_dir.rglob('plugin.json'), None)
    if not plugin_json:
        return web.json_response({'error': 'Invalid plugin package'}, status=400)
        
    # Load plugin metadata
    plugin_metadata = json.loads(plugin_json.read_text())
    plugin_name = plugin_metadata.get('name')
    
    if not plugin_name:
        return web.json_response({'error': 'Plugin name not found'}, status=400)
        
    # Check if plugin already exists
    if PluginModel.select().where(PluginModel.name == plugin_name).exists():
        return web.json_response({'error': 'Plugin already exists'}, status=400)
        
    # Copy to plugins directory
    plugin_dir = studio.engine.base_dir / 'plugins' / plugin_name
    shutil.copytree(plugin_json.parent, plugin_dir, dirs_exist_ok=True)
    
    # Create plugin record
    plugin = PluginModel.create(
        name=plugin_name,
        version=plugin_metadata.get('version', '1.0.0'),
        description=plugin_metadata.get('description', ''),
        author=plugin_metadata.get('author', 'Unknown'),
        url=plugin_metadata.get('url'),
        category=plugin_metadata.get('category', 'general'),
        dependencies=json.dumps(plugin_metadata.get('dependencies', [])),
    )
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    return web.json_response({
        'success': True,
        'plugin': plugin.to_dict(),
    })

async def plugin_settings(request: web.Request):
    """Get plugin settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        return web.json_response({
            'success': True,
            'settings': plugin.get_settings(),
        })
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)

async def update_plugin_settings(request: web.Request):
    """Update plugin settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    plugin_id = request.match_info['plugin_id']
    data = await request.json()
    
    try:
        plugin_uuid = uuid.UUID(plugin_id)
        plugin = PluginModel.get_by_id(plugin_uuid)
        plugin.update_settings(data.get('settings', {}))
        
        return web.json_response({
            'success': True,
            'settings': plugin.get_settings(),
        })
    except (ValueError, PluginModel.DoesNotExist):
        return web.json_response({'error': 'Plugin not found'}, status=404)