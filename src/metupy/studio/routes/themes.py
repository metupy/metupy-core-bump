# metupy/studio/routes/theme_routes.py
"""Theme Routes untuk Studio."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
from metupy import studio
from metupy.models.theme import ThemeModel
from metupy.models.activity import ActivityLogModel
import uuid
import json
from pathlib import Path
import shutil

def setup(app: web.Application, studio):
    """Setup theme routes."""
    app.router.add_get('/dashboard/themes', themes_list)
    app.router.add_get('/dashboard/themes/{theme_id}', theme_detail)
    app.router.add_post('/dashboard/themes/{theme_id}/activate', activate_theme)
    app.router.add_post('/dashboard/themes/{theme_id}/deactivate', deactivate_theme)
    app.router.add_delete('/dashboard/themes/{theme_id}', delete_theme)
    app.router.add_get('/dashboard/themes/{theme_id}/preview', preview_theme)
    app.router.add_post('/dashboard/themes/upload', upload_theme)
    app.router.add_get('/dashboard/themes/{theme_id}/export', export_theme)

async def themes_list(request: web.Request):
    """List all themes."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    themes = ThemeModel.select()
    
    context = {
        'title': 'Themes',
        'active_page': 'themes',
        'themes': [t.to_dict() for t in themes],
        'current_theme': studio.engine.config.ACTIVE_THEME,
    }
    return render_template('dashboard/themes/list.html', request, context)

async def theme_detail(request: web.Request):
    """Theme detail page."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    theme_id = request.match_info['theme_id']
    
    try:
        theme_uuid = uuid.UUID(theme_id)
        theme = ThemeModel.get_by_id(theme_uuid)
    except (ValueError, ThemeModel.DoesNotExist):
        return web.Response(text='Theme not found', status=404)
        
    context = {
        'title': f'Theme: {theme.name}',
        'active_page': 'themes',
        'theme': theme.to_dict(),
    }
    return render_template('dashboard/themes/detail.html', request, context)

async def activate_theme(request: web.Request):
    """Activate theme."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    theme_id = request.match_info['theme_id']
    
    try:
        theme_uuid = uuid.UUID(theme_id)
        theme = ThemeModel.get_by_id(theme_uuid)
        
        # Deactivate all themes
        ThemeModel.update(is_active=False).execute()
        
        # Activate selected theme
        theme.is_active = True
        theme.save()
        
        # Update config
        await update_config_theme(theme.name)
        
        # Reload theme in engine
        await studio.engine.theme_manager.load_theme()
        
        # Log activity
        ActivityLogModel.create(
            user_id=user_id,
            action='activate',
            entity_type='theme',
            entity_id=str(theme.id),
            description=f'Activated theme: {theme.name}',
        )
        
        return web.json_response({'success': True})
    except (ValueError, ThemeModel.DoesNotExist):
        return web.json_response({'error': 'Theme not found'}, status=404)

async def deactivate_theme(request: web.Request):
    """Deactivate theme."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    theme_id = request.match_info['theme_id']
    
    try:
        theme_uuid = uuid.UUID(theme_id)
        theme = ThemeModel.get_by_id(theme_uuid)
        theme.is_active = False
        theme.save()
        
        return web.json_response({'success': True})
    except (ValueError, ThemeModel.DoesNotExist):
        return web.json_response({'error': 'Theme not found'}, status=404)

async def delete_theme(request: web.Request):
    """Delete theme."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    theme_id = request.match_info['theme_id']
    
    try:
        theme_uuid = uuid.UUID(theme_id)
        theme = ThemeModel.get_by_id(theme_uuid)
        
        # Don't delete active theme
        if theme.is_active:
            return web.json_response({'error': 'Cannot delete active theme'}, status=400)
            
        # Delete theme directory
        theme_dir = studio.engine.base_dir / 'themes' / theme.name
        if theme_dir.exists():
            shutil.rmtree(theme_dir)
            
        theme.delete_instance()
        
        return web.json_response({'success': True})
    except (ValueError, ThemeModel.DoesNotExist):
        return web.json_response({'error': 'Theme not found'}, status=404)

async def preview_theme(request: web.Request):
    """Preview theme."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    theme_id = request.match_info['theme_id']
    
    try:
        theme_uuid = uuid.UUID(theme_id)
        theme = ThemeModel.get_by_id(theme_uuid)
        
        # Generate preview URL
        preview_url = f"/preview/{theme.name}"
        
        return web.json_response({
            'success': True,
            'preview_url': preview_url,
        })
    except (ValueError, ThemeModel.DoesNotExist):
        return web.json_response({'error': 'Theme not found'}, status=404)

async def upload_theme(request: web.Request):
    """Upload theme."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.post()
    theme_file = data.get('theme_file')
    
    if not theme_file:
        return web.json_response({'error': 'No file uploaded'}, status=400)
        
    # Save uploaded file
    import zipfile
    import tempfile
    
    temp_dir = Path(tempfile.mkdtemp())
    zip_path = temp_dir / 'theme.zip'
    
    zip_path.write_bytes(theme_file.file.read())
    
    # Extract zip
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        
    # Find theme.json
    theme_json = next(temp_dir.rglob('theme.json'), None)
    if not theme_json:
        return web.json_response({'error': 'Invalid theme package'}, status=400)
        
    # Load theme metadata
    theme_metadata = json.loads(theme_json.read_text())
    theme_name = theme_metadata.get('name')
    
    if not theme_name:
        return web.json_response({'error': 'Theme name not found'}, status=400)
        
    # Copy to themes directory
    theme_dir = studio.engine.base_dir / 'themes' / theme_name
    shutil.copytree(theme_json.parent, theme_dir, dirs_exist_ok=True)
    
    # Create theme record
    theme = ThemeModel.create(
        name=theme_name,
        version=theme_metadata.get('version', '1.0.0'),
        description=theme_metadata.get('description', ''),
        author=theme_metadata.get('author', 'Unknown'),
    )
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    return web.json_response({
        'success': True,
        'theme': theme.to_dict(),
    })

async def export_theme(request: web.Request):
    """Export theme."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    theme_id = request.match_info['theme_id']
    
    try:
        theme_uuid = uuid.UUID(theme_id)
        theme = ThemeModel.get_by_id(theme_uuid)
        
        # Create zip
        import zipfile
        import io
        
        theme_dir = studio.engine.base_dir / 'themes' / theme.name
        
        if not theme_dir.exists():
            return web.json_response({'error': 'Theme directory not found'}, status=404)
            
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in theme_dir.rglob('*'):
                if file_path.is_file():
                    zip_file.write(file_path, file_path.relative_to(theme_dir))
                    
        return web.Response(
            body=zip_buffer.getvalue(),
            headers={
                'Content-Type': 'application/zip',
                'Content-Disposition': f'attachment; filename="{theme.name}.zip"',
            }
        )
    except (ValueError, ThemeModel.DoesNotExist):
        return web.json_response({'error': 'Theme not found'}, status=404)

async def update_config_theme(theme_name: str):
    """Update theme in config."""
    config_file = studio.engine.base_dir / 'pymconfig.py'
    content = config_file.read_text()
    
    import re
    content = re.sub(
        r'ACTIVE_THEME\s*=\s*"[^"]*"',
        f'ACTIVE_THEME = "{theme_name}"',
        content
    )
    
    config_file.write_text(content)