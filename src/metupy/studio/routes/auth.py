# metupy/studio/routes/auth_routes.py
"""Authentication Routes."""

from aiohttp import web
from aiohttp_jinja2 import render_template
from aiohttp_session import get_session
from aiohttp_security import remember, forget, authorized_userid

from metupy import studio

def setup(app: web.Application, studio):
    """Setup auth routes."""
    app.router.add_get('/login', login_page)
    app.router.add_post('/login', login)
    app.router.add_get('/logout', logout)
    app.router.add_get('/register', register_page)
    app.router.add_post('/register', register)
    app.router.add_get('/forgot-password', forgot_password_page)
    app.router.add_post('/forgot-password', forgot_password)
    app.router.add_get('/reset-password', reset_password_page)
    app.router.add_post('/reset-password', reset_password)

async def login_page(request: web.Request):
    """Login page."""
    context = {
        'title': 'Login',
    }
    return render_template('auth/login.html', request, context)

async def login(request: web.Request):
    """Process login."""
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return web.json_response({
            'success': False,
            'error': 'Username and password required'
        }, status=400)
        
    # Find user
    from metupy.models.user import User
    try:
        user = User.get(User.username == username)
    except User.DoesNotExist:
        return web.json_response({
            'success': False,
            'error': 'Invalid credentials'
        }, status=401)
        
    # Check password
    if not user.check_password(password):
        return web.json_response({
            'success': False,
            'error': 'Invalid credentials'
        }, status=401)
        
    # Check if active
    if not user.is_active:
        return web.json_response({
            'success': False,
            'error': 'Account is inactive'
        }, status=403)
        
    # Update last login
    from datetime import datetime
    user.last_login = datetime.now()
    user.save()
    
    # Create session
    session = await get_session(request)
    session['user_id'] = user.id
    session['username'] = user.username
    
    return web.json_response({
        'success': True,
        'redirect': '/dashboard'
    })

async def logout(request: web.Request):
    """Logout."""
    session = await get_session(request)
    session.clear()
    
    raise web.HTTPFound('/login')

async def register_page(request: web.Request):
    """Register page."""
    context = {
        'title': 'Register',
    }
    return render_template('auth/register.html', request, context)

async def register(request: web.Request):
    """Process registration."""
    data = await request.json()
    
    # Validate
    required = ['username', 'email', 'password', 'password_confirm']
    for field in required:
        if field not in data:
            return web.json_response({
                'success': False,
                'error': f'Missing field: {field}'
            }, status=400)
            
    # Check passwords match
    if data['password'] != data['password_confirm']:
        return web.json_response({
            'success': False,
            'error': 'Passwords do not match'
        }, status=400)
        
    # Check username availability
    from metupy.models.user import User
    if User.select().where(User.username == data['username']).exists():
        return web.json_response({
            'success': False,
            'error': 'Username already taken'
        }, status=400)
        
    # Create user
    user = User.create(
        username=data['username'],
        email=data['email'],
        password_hash=User.hash_password(data['password']),
    )
    
    return web.json_response({
        'success': True,
        'redirect': '/login'
    })

async def forgot_password_page(request: web.Request):
    """Forgot password page."""
    context = {'title': 'Forgot Password'}
    return render_template('auth/forgot-password.html', request, context)

async def forgot_password(request: web.Request):
    """Process forgot password."""
    data = await request.json()
    email = data.get('email')
    
    # Find user by email
    from metupy.models.user import User
    try:
        user = User.get(User.email == email)
    except User.DoesNotExist:
        # Don't reveal if email exists
        return web.json_response({'success': True})
        
    # Generate reset token
    token = studio.security.generate_token({'user_id': user.id}, expiry=3600)
    
    # Send email (implementation needed)
    await send_reset_email(email, token)
    
    return web.json_response({'success': True})

async def reset_password_page(request: web.Request):
    """Reset password page."""
    token = request.query.get('token')
    
    # Verify token
    data = studio.security.verify_token(token)
    if not data:
        return web.Response(text='Invalid or expired token', status=400)
        
    context = {
        'title': 'Reset Password',
        'token': token,
    }
    return render_template('auth/reset-password.html', request, context)

async def reset_password(request: web.Request):
    """Process reset password."""
    data = await request.json()
    token = data.get('token')
    new_password = data.get('password')
    
    # Verify token
    token_data = studio.security.verify_token(token)
    if not token_data:
        return web.json_response({
            'success': False,
            'error': 'Invalid or expired token'
        }, status=400)
        
    # Update password
    from metupy.models.user import User
    user = User.get_by_id(token_data['user_id'])
    user.set_password(new_password)
    user.save()
    
    return web.json_response({'success': True})

async def send_reset_email(email: str, token: str):
    """Send password reset email."""
    # Implementation for sending email
    pass