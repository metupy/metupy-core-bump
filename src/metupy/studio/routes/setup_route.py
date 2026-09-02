# metupy/studio/routes/setup_routes.py
"""Setup Wizard Routes."""

from aiohttp import web
from aiohttp_jinja2 import render_template
import json
from pathlib import Path

from aiohttp_session import get_session

from metupy import studio

def setup(app: web.Application, studio):
    """Setup routes."""
    app.router.add_get('/setup', setup_wizard)
    app.router.add_post('/setup/step1', setup_step1)
    app.router.add_post('/setup/step2', setup_step2)
    app.router.add_post('/setup/step3', setup_step3)
    app.router.add_post('/setup/step4', setup_step4)
    app.router.add_post('/setup/complete', setup_complete)
    app.router.add_get('/setup/check', check_setup_status)

async def setup_wizard(request: web.Request):
    """Setup wizard page."""
    # Check if already setup
    if studio.is_setup_complete():
        raise web.HTTPFound('/login')
        
    context = {
        'title': 'Setup Wizard',
        'steps': ['Basic Info', 'Database', 'Admin Account', 'Theme', 'Install'],
        'current_step': 1,
    }
    return render_template('setup/wizard.html', request, context)

async def setup_step1(request: web.Request):
    """Process basic info step."""
    data = await request.json()
    
    # Validate data
    required_fields = ['site_name', 'site_url', 'site_description']
    for field in required_fields:
        if field not in data or not data[field]:
            return web.json_response({
                'success': False,
                'error': f'Missing required field: {field}'
            }, status=400)
            
    # Store in session
    session = await get_session(request)
    session['setup'] = session.get('setup', {})
    session['setup']['basic_info'] = data
    
    return web.json_response({'success': True})

async def setup_step2(request: web.Request):
    """Process database config step."""
    data = await request.json()
    
    # Validate database config
    db_type = data.get('db_type', 'sqlite')
    
    if db_type != 'sqlite':
        required_fields = ['db_host', 'db_user', 'db_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return web.json_response({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
                
    # Test database connection
    try:
        await test_database_connection(data)
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': f'Database connection failed: {str(e)}'
        }, status=400)
        
    # Store in session
    session = await get_session(request)
    session['setup'] = session.get('setup', {})
    session['setup']['database'] = data
    
    return web.json_response({'success': True})

async def setup_step3(request: web.Request):
    """Process admin account step."""
    data = await request.json()
    
    # Validate admin account
    required_fields = ['username', 'email', 'password', 'password_confirm']
    for field in required_fields:
        if field not in data or not data[field]:
            return web.json_response({
                'success': False,
                'error': f'Missing required field: {field}'
            }, status=400)
            
    # Check password match
    if data['password'] != data['password_confirm']:
        return web.json_response({
            'success': False,
            'error': 'Passwords do not match'
        }, status=400)
        
    # Check password strength
    if len(data['password']) < 8:
        return web.json_response({
            'success': False,
            'error': 'Password must be at least 8 characters'
        }, status=400)
        
    # Hash password
    from metupy.core.security import SecurityManager
    security = SecurityManager(studio.engine)
    data['password_hash'] = security.hash_password(data['password'])
    del data['password']
    del data['password_confirm']
    
    # Store in session
    session = await get_session(request)
    session['setup'] = session.get('setup', {})
    session['setup']['admin'] = data
    
    return web.json_response({'success': True})

async def setup_step4(request: web.Request):
    """Process theme selection step."""
    data = await request.json()
    
    # Validate theme
    theme_name = data.get('theme', 'default')
    if theme_name not in studio.engine.theme_manager.list_themes():
        return web.json_response({
            'success': False,
            'error': f'Invalid theme: {theme_name}'
        }, status=400)
        
    # Store in session
    session = await get_session(request)
    session['setup'] = session.get('setup', {})
    session['setup']['theme'] = data
    
    return web.json_response({'success': True})

async def setup_complete(request: web.Request):
    """Complete setup."""
    session = await get_session(request)
    setup_data = session.get('setup', {})
    
    if not setup_data:
        return web.json_response({
            'success': False,
            'error': 'No setup data found'
        }, status=400)
        
    try:
        # Apply configuration
        await apply_configuration(setup_data)
        
        # Create admin user
        await create_admin_user(setup_data['admin'])
        
        # Mark setup as complete
        await mark_setup_complete()
        
        # Clear setup session
        session.pop('setup', None)
        
        return web.json_response({
            'success': True,
            'redirect': '/login'
        })
        
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': f'Setup failed: {str(e)}'
        }, status=500)

async def check_setup_status(request: web.Request):
    """Check setup status."""
    return web.json_response({
        'setup_complete': studio.is_setup_complete()
    })

async def test_database_connection(config: dict):
    """Test database connection."""
    # Implementation for testing database connection
    pass

async def apply_configuration(setup_data: dict):
    """Apply configuration to pymconfig.py."""
    config_file = studio.engine.base_dir / 'pymconfig.py'
    
    # Read existing config
    content = config_file.read_text()
    
    # Update site info
    basic_info = setup_data.get('basic_info', {})
    content = update_config_value(content, 'SITE_NAME', basic_info.get('site_name'))
    content = update_config_value(content, 'SITE_URL', basic_info.get('site_url'))
    content = update_config_value(content, 'SITE_DESCRIPTION', basic_info.get('site_description'))
    
    # Update database config
    db_config = setup_data.get('database', {})
    content = update_config_value(content, 'DB_ENGINE', db_config.get('db_type', 'sqlite'))
    
    # Update theme
    theme_config = setup_data.get('theme', {})
    content = update_config_value(content, 'ACTIVE_THEME', theme_config.get('theme', 'default'))
    
    # Write updated config
    config_file.write_text(content)
    
async def create_admin_user(admin_data: dict):
    """Create admin user."""
    from metupy.models.user import User
    
    user = User.create(
        username=admin_data['username'],
        email=admin_data['email'],
        password_hash=admin_data['password_hash'],
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    
async def mark_setup_complete():
    """Mark setup as complete."""
    # Create setup flag file
    setup_flag = studio.engine.base_dir / 'data' / '.setup_complete'
    setup_flag.touch()
    
def update_config_value(content: str, key: str, value) -> str:
    """Update config value in pymconfig.py."""
    import re
    
    # Quote string values
    if isinstance(value, str):
        value = f'"{value}"'
        
    # Update or add value
    pattern = f'^{key}\\s*=.*$'
    replacement = f'{key} = {value}'
    
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f'\n{replacement}'
        
    return content