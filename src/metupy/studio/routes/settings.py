# metupy/studio/routes/settings_routes.py
"""Settings Routes untuk Studio."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import authorized_userid
from metupy import studio
from metupy.models.activity import ActivityLogModel
import json
import re

def setup(app: web.Application, studio):
    """Setup settings routes."""
    app.router.add_get('/dashboard/settings', settings_page)
    app.router.add_post('/dashboard/settings/site', update_site_settings)
    app.router.add_post('/dashboard/settings/build', update_build_settings)
    app.router.add_post('/dashboard/settings/server', update_server_settings)
    app.router.add_post('/dashboard/settings/database', update_database_settings)
    app.router.add_post('/dashboard/settings/cache', update_cache_settings)
    app.router.add_post('/dashboard/settings/security', update_security_settings)
    app.router.add_get('/dashboard/settings/export', export_settings)
    app.router.add_post('/dashboard/settings/import', import_settings)

async def settings_page(request: web.Request):
    """Settings page."""
    user_id = await authorized_userid(request)
    if not user_id:
        raise web.HTTPFound('/login')
        
    context = {
        'title': 'Settings',
        'active_page': 'settings',
        'config': studio.engine.config.get_all(),
    }
    return render_template('dashboard/settings/index.html', request, context)

async def update_site_settings(request: web.Request):
    """Update site settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    # Update config
    updates = {
        'SITE_NAME': data.get('site_name'),
        'SITE_URL': data.get('site_url'),
        'SITE_DESCRIPTION': data.get('site_description'),
        'SITE_AUTHOR': data.get('site_author'),
        'SITE_KEYWORDS': data.get('site_keywords'),
        'SITE_LANG': data.get('site_lang'),
        'SITE_TIMEZONE': data.get('site_timezone'),
    }
    
    await update_config(updates)
    
    # Log activity
    ActivityLogModel.create(
        user_id=user_id,
        action='update',
        entity_type='settings',
        entity_id='site',
        description='Updated site settings',
    )
    
    return web.json_response({'success': True})

async def update_build_settings(request: web.Request):
    """Update build settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    updates = {
        'BUILD_MINIFY_HTML': data.get('minify_html', False),
        'BUILD_MINIFY_CSS': data.get('minify_css', False),
        'BUILD_MINIFY_JS': data.get('minify_js', False),
        'BUILD_GENERATE_SITEMAP': data.get('generate_sitemap', True),
        'BUILD_GENERATE_FEED': data.get('generate_feed', True),
        'BUILD_CACHE_ENABLED': data.get('cache_enabled', True),
        'BUILD_PRETTY_URLS': data.get('pretty_urls', True),
    }
    
    await update_config(updates)
    
    return web.json_response({'success': True})

async def update_server_settings(request: web.Request):
    """Update server settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    updates = {
        'DEV_HOST': data.get('host', 'localhost'),
        'DEV_PORT': int(data.get('port', 3000)),
        'DEV_DEBUG': data.get('debug', True),
        'DEV_LIVE_RELOAD': data.get('live_reload', True),
    }
    
    await update_config(updates)
    
    return web.json_response({'success': True})

async def update_database_settings(request: web.Request):
    """Update database settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    updates = {
        'DB_ENGINE': data.get('engine', 'sqlite'),
        'DB_HOST': data.get('host', 'localhost'),
        'DB_PORT': int(data.get('port', 5432)),
        'DB_USER': data.get('user', ''),
        'DB_NAME': data.get('name', 'metupy_db'),
    }
    
    await update_config(updates)
    
    return web.json_response({'success': True})

async def update_cache_settings(request: web.Request):
    """Update cache settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    updates = {
        'CACHE_ENABLED': data.get('enabled', True),
        'CACHE_TYPE': data.get('type', 'redis'),
        'CACHE_HOST': data.get('host', 'localhost'),
        'CACHE_PORT': int(data.get('port', 6379)),
        'CACHE_TTL': int(data.get('ttl', 3600)),
    }
    
    await update_config(updates)
    
    return web.json_response({'success': True})

async def update_security_settings(request: web.Request):
    """Update security settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    updates = {
        'CSRF_ENABLED': data.get('csrf_enabled', True),
        'CORS_ENABLED': data.get('cors_enabled', True),
    }
    
    await update_config(updates)
    
    return web.json_response({'success': True})

async def update_config(updates: dict):
    """Update config file."""
    config_file = studio.engine.base_dir / 'pymconfig.py'
    content = config_file.read_text()
    
    for key, value in updates.items():
        if value is not None:
            # Format value
            if isinstance(value, str):
                formatted = f'"{value}"'
            elif isinstance(value, list):
                formatted = str(value)
            elif isinstance(value, bool):
                formatted = str(value)
            else:
                formatted = str(value)
                
            # Update or add
            pattern = f'^{key}\\s*=.*$'
            replacement = f'{key} = {formatted}'
            
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content += f'\n{replacement}'
                
    config_file.write_text(content)
    
    # Reload config
    studio.engine.config.reload()

async def export_settings(request: web.Request):
    """Export settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    config = studio.engine.config.get_all()
    
    return web.json_response({
        'success': True,
        'config': config,
    })

async def import_settings(request: web.Request):
    """Import settings."""
    user_id = await authorized_userid(request)
    if not user_id:
        return web.json_response({'error': 'Unauthorized'}, status=401)
        
    data = await request.json()
    
    await update_config(data)
    
    return web.json_response({'success': True})