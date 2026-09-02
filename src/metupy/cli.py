# metupy/cli.py
"""Metupy CLI - Command Line Interface (pym)."""

import argparse
import asyncio
import sys
import json
import shutil
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
from rich.prompt import Confirm, Prompt
from rich.tree import Tree
from rich.markdown import Markdown

console = Console()

def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog='pym',
        description='Metupy - Markdown Engine Template Utilities Python',
        epilog='For more information, visit: https://metupy.dev',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='pym 1.0.0 (Metupy)',
        help='Show version information'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # serve command (preview)
    serve_parser = subparsers.add_parser(
        'serve',
        help='Serve site with livereload',
        description='Start development server with live reload'
    )
    serve_parser.add_argument('--host', default='localhost', help='Host to bind (default: localhost)')
    serve_parser.add_argument('--port', type=int, default=3155, help='Port to bind (default: 3155)')
    serve_parser.add_argument('--no-livereload', action='store_true', help='Disable live reload')
    serve_parser.add_argument('--open-browser', action='store_true', help='Open browser automatically')
    serve_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # build command
    build_parser = subparsers.add_parser(
        'build',
        help='Build static site',
        description='Generate static site to output directory'
    )
    build_parser.add_argument('--output', '-o', default='public', help='Output directory (default: public)')
    build_parser.add_argument('--clean', action='store_true', help='Clean output directory before build')
    build_parser.add_argument('--minify', action='store_true', help='Minify HTML, CSS, and JS')
    build_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed build information')
    build_parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    
    # studio command
    studio_parser = subparsers.add_parser(
        'studio',
        help='Open Metupy Studio',
        description='Start Metupy Studio CMS'
    )
    studio_parser.add_argument('--port', type=int, default=3154, help='Port for studio (default: 3154)')
    studio_parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    studio_parser.add_argument('--host', default='localhost', help='Host to bind (default: localhost)')
    
    # init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize new Metupy project',
        description='Create new Metupy project structure'
    )
    init_parser.add_argument('--name', help='Project name')
    init_parser.add_argument('--template', choices=['blog', 'docs', 'landing', 'slides', 'basic'], default='basic', help='Project template (default: basic)')
    init_parser.add_argument('--force', action='store_true', help='Force creation even if directory exists')
    
    # new command
    new_parser = subparsers.add_parser(
        'new',
        help='Create new content',
        description='Create new page, post, or content'
    )
    new_subparsers = new_parser.add_subparsers(dest='content_type', help='Content type')
    
    # new page
    new_page_parser = new_subparsers.add_parser('page', help='Create new page')
    new_page_parser.add_argument('name', help='Page name')
    new_page_parser.add_argument('--template', default='default', help='Template to use')
    new_page_parser.add_argument('--type', default='page', help='Page type (page, post, docs)')
    
    # new post
    new_post_parser = new_subparsers.add_parser('post', help='Create new blog post')
    new_post_parser.add_argument('title', help='Post title')
    new_post_parser.add_argument('--slug', help='Post slug (default: generated from title)')
    new_post_parser.add_argument('--tags', help='Comma-separated tags')
    new_post_parser.add_argument('--author', help='Post author')
    
    # new theme
    new_theme_parser = new_subparsers.add_parser('theme', help='Create new theme')
    new_theme_parser.add_argument('name', help='Theme name')
    new_theme_parser.add_argument('--description', help='Theme description')
    
    # new plugin
    new_plugin_parser = new_subparsers.add_parser('plugin', help='Create new plugin')
    new_plugin_parser.add_argument('name', help='Plugin name')
    new_plugin_parser.add_argument('--description', help='Plugin description')
    
    # new widget
    new_widget_parser = new_subparsers.add_parser('widget', help='Create new widget')
    new_widget_parser.add_argument('name', help='Widget name')
    new_widget_parser.add_argument('--description', help='Widget description')
    
    # clean command
    clean_parser = subparsers.add_parser(
        'clean',
        help='Clean output directory',
        description='Remove all generated files'
    )
    clean_parser.add_argument('--output', '-o', default='public', help='Output directory (default: public)')
    clean_parser.add_argument('--all', action='store_true', help='Also clean cache and data')
    
    # plugin commands
    plugin_parser = subparsers.add_parser(
        'plugin',
        help='Manage plugins',
        description='Install, remove, or list plugins'
    )
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_action', help='Plugin action')
    
    plugin_list_parser = plugin_subparsers.add_parser('list', help='List installed plugins')
    plugin_list_parser.add_argument('--active', action='store_true', help='Show only active plugins')
    
    plugin_install_parser = plugin_subparsers.add_parser('install', help='Install plugin')
    plugin_install_parser.add_argument('name', help='Plugin name')
    plugin_install_parser.add_argument('--source', choices=['pypi', 'github', 'local'], default='pypi', help='Plugin source')
    plugin_install_parser.add_argument('--version', help='Plugin version')
    
    plugin_remove_parser = plugin_subparsers.add_parser('remove', help='Remove plugin')
    plugin_remove_parser.add_argument('name', help='Plugin name')
    plugin_remove_parser.add_argument('--force', action='store_true', help='Force removal')
    
    plugin_enable_parser = plugin_subparsers.add_parser('enable', help='Enable plugin')
    plugin_enable_parser.add_argument('name', help='Plugin name')
    
    plugin_disable_parser = plugin_subparsers.add_parser('disable', help='Disable plugin')
    plugin_disable_parser.add_argument('name', help='Plugin name')
    
    # theme commands
    theme_parser = subparsers.add_parser(
        'theme',
        help='Manage themes',
        description='Install, remove, or list themes'
    )
    theme_subparsers = theme_parser.add_subparsers(dest='theme_action', help='Theme action')
    
    theme_list_parser = theme_subparsers.add_parser('list', help='List installed themes')
    
    theme_install_parser = theme_subparsers.add_parser('install', help='Install theme')
    theme_install_parser.add_argument('name', help='Theme name')
    theme_install_parser.add_argument('--source', choices=['pypi', 'github', 'local'], default='pypi', help='Theme source')
    
    theme_create_parser = theme_subparsers.add_parser('create', help='Create new theme')
    theme_create_parser.add_argument('name', help='Theme name')
    
    theme_activate_parser = theme_subparsers.add_parser('activate', help='Activate theme')
    theme_activate_parser.add_argument('name', help='Theme name')
    
    # config command
    config_parser = subparsers.add_parser(
        'config',
        help='Manage configuration',
        description='View or edit configuration'
    )
    config_subparsers = config_parser.add_subparsers(dest='config_action', help='Config action')
    
    config_show_parser = config_subparsers.add_parser('show', help='Show current configuration')
    config_show_parser.add_argument('--key', help='Show specific config key')
    
    config_set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    config_set_parser.add_argument('key', help='Config key')
    config_set_parser.add_argument('value', help='Config value')
    
    # info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show project information',
        description='Display information about the current project'
    )
    
    return parser


# ═══ Command Handlers ═══

def cmd_serve(args):
    """Handle serve command."""
    console.print(Panel.fit(
        "[bold cyan]Metupy[/bold cyan] - Development Server",
        border_style="blue"
    ))
    
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config
    
    config = get_config()
    
    # Override config with CLI args
    if hasattr(config, 'DEV_HOST'):
        config.DEV_HOST = args.host
    if hasattr(config, 'DEV_PORT'):
        config.DEV_PORT = args.port
    if hasattr(config, 'DEV_LIVE_RELOAD'):
        config.DEV_LIVE_RELOAD = not args.no_livereload
    if hasattr(config, 'DEV_DEBUG'):
        config.DEV_DEBUG = args.debug
    
    engine = MetupyEngine()
    
    console.print(f"[green]➜[/green] Starting server at [bold]http://{args.host}:{args.port}[/bold]")
    
    if args.open_browser:
        import threading
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://{args.host}:{args.port}')
        threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        # Gunakan asyncio.run() untuk manage event loop
        asyncio.run(engine.serve())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        

def cmd_build(args):
    """Handle build command."""
    console.print(Panel.fit(
        "[bold cyan]Metupy[/bold cyan] - Building Static Site",
        border_style="blue"
    ))
    
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config
    
    config = get_config()
    
    if hasattr(config, 'OUTPUT_DIR'):
        config.OUTPUT_DIR = Path(args.output)
    if hasattr(config, 'BUILD_MINIFY_HTML'):
        config.BUILD_MINIFY_HTML = args.minify
        config.BUILD_MINIFY_CSS = args.minify
        config.BUILD_MINIFY_JS = args.minify
    if hasattr(config, 'BUILD_CACHE_ENABLED'):
        config.BUILD_CACHE_ENABLED = not args.no_cache
    
    if args.clean:
        clean_output(args.output)
    
    engine = MetupyEngine()
    
    try:
        result = asyncio.run(engine.build())
        
        if result:
            console.print(f"[green]✓[/green] Build completed successfully!")
            console.print(f"[green]✓[/green] Output: [bold]{args.output}[/bold]")
            
            if args.verbose:
                table = Table(title="Build Statistics")
                table.add_column("Item", style="cyan")
                table.add_column("Value", style="magenta")
                table.add_row("Pages Built", str(result.get('pages_built', 0)))
                table.add_row("Build Time", result.get('build_time', '0s'))
                table.add_row("Output Size", result.get('output_size', '0 B'))
                console.print(table)
        else:
            console.print("[red]✗[/red] Build failed!")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_studio(args):
    """Handle studio command."""
    console.print(Panel.fit(
        "[bold magenta]Metupy Studio[/bold magenta] - Content Management System",
        border_style="purple"
    ))
    
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config
    
    config = get_config()
    
    if hasattr(config, 'STUDIO_PORT'):
        config.STUDIO_PORT = args.port
    if hasattr(config, 'STUDIO_HOST'):
        config.STUDIO_HOST = args.host
    if hasattr(config, 'STUDIO_AUTO_OPEN'):
        config.STUDIO_AUTO_OPEN = not args.no_browser
    
    engine = MetupyEngine()
    
    console.print(f"[green]➜[/green] Starting Studio at [bold]http://{args.host}:{args.port}[/bold]")
    
    if not args.no_browser:
        import threading
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://{args.host}:{args.port}')
        threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        asyncio.run(engine.start_studio())
    except KeyboardInterrupt:
        console.print("\n[yellow]Studio stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    """Handle studio command."""
    console.print(Panel.fit(
        "[bold magenta]Metupy Studio[/bold magenta] - Content Management System",
        border_style="purple"
    ))
    
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config
    
    config = get_config()
    
    if hasattr(config, 'STUDIO_PORT'):
        config.STUDIO_PORT = args.port
    if hasattr(config, 'STUDIO_HOST'):
        config.STUDIO_HOST = args.host
    if hasattr(config, 'STUDIO_AUTO_OPEN'):
        config.STUDIO_AUTO_OPEN = not args.no_browser
    
    engine = MetupyEngine()
    
    console.print(f"[green]➜[/green] Starting Studio at [bold]http://{args.host}:{args.port}[/bold]")
    
    try:
        asyncio.run(engine.start_studio())
    except KeyboardInterrupt:
        console.print("\n[yellow]Studio stopped[/yellow]")


def cmd_init(args):
    """Handle init command."""
    project_name = args.name or Path.cwd().name
    
    console.print(f"[bold]Creating Metupy project: {project_name}[/bold]\n")
    
    # Check if directory exists
    project_dir = Path(project_name)
    if project_dir.exists() and not args.force:
        if not Confirm.ask(f"Directory '{project_name}' already exists. Continue?"):
            return
    
    # Create project structure
    directories = [
        'pages',
        'content',
        'content/blog',
        'content/docs',
        'content/assets',
        'content/assets/images',
        'content/assets/css',
        'content/assets/js',
        'themes',
        'themes/default',
        'themes/default/templates',
        'themes/default/static',
        'plugins',
        'widgets',
        'public',
        'data',
        'data/comments',
        'static',
        'static/css',
        'static/js',
        'static/images',
        'templates',
        'locales',
    ]
    
    tree = Tree(f"[bold cyan]{project_name}[/bold cyan]")
    
    for directory in directories:
        dir_path = project_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Add to tree
        parts = directory.split('/')
        current = tree
        for part in parts:
            found = False
            for child in current.children:
                if child.label == part:
                    current = child
                    found = True
                    break
            if not found:
                current = current.add(part)
    
    # Create pymconfig.py
    config_content = create_config_content(project_name)
    (project_dir / 'pymconfig.py').write_text(config_content)
    tree.add('pymconfig.py')
    
    # Create theme.json for default theme
    theme_config = {
        "name": "default",
        "version": "1.0.0",
        "description": "Default Metupy Theme",
        "author": "Metupy Team",
    }
    (project_dir / 'themes' / 'default' / 'theme.json').write_text(json.dumps(theme_config, indent=2))
    
    # Create default template
    default_template = create_default_template()
    (project_dir / 'themes' / 'default' / 'templates' / 'default.html').write_text(default_template)
    
    # Create sample pages based on template
    if args.template == 'blog':
        create_blog_template(project_dir, tree)
    elif args.template == 'docs':
        create_docs_template(project_dir, tree)
    elif args.template == 'landing':
        create_landing_template(project_dir, tree)
    elif args.template == 'slides':
        create_slides_template(project_dir, tree)
    else:
        create_basic_template(project_dir, tree)
    
    # Create .gitignore
    gitignore_content = """# Metupy
public/
__pycache__/
*.pyc
.env
data/*.db
.DS_Store
"""
    (project_dir / '.gitignore').write_text(gitignore_content)
    tree.add('.gitignore')
    
    # Create README.md
    readme_content = f"""# {project_name}

Built with Metupy SSG.

## Getting Started

    pym serve
    pym build
    pym studio
"""
    (project_dir / 'README.md').write_text(readme_content)
    tree.add('README.md')
    
    console.print(tree)
    console.print("\n[green]✓ Project created successfully![/green]")
    console.print(f"\nNext steps:")
    console.print(f"  cd {project_name}")
    console.print("  pym serve --open-browser")
    console.print("  pym studio")


def create_config_content(project_name: str) -> str:
    """Create pymconfig.py content."""
    return f'''"""pymconfig.py - Metupy Project Configuration File.

Edit values below to configure your site.
All variables MUST be UPPERCASE.
"""

import os
from pathlib import Path

# Site Information
SITE_NAME = "{project_name}"
SITE_VERSION = "1.0.0"
SITE_DESCRIPTION = "Built with Metupy SSG"
SITE_AUTHOR = "Your Name"
SITE_KEYWORDS = ["metupy", "static-site", "ssg"]
SITE_LANG = "en"
SITE_TIMEZONE = "UTC"

# Site URL (preview/serve)
SITE_URL = "http://localhost:3155"
SITE_BASE_URL = "/"
SITE_CANONICAL_URL = f"{{SITE_URL}}/"

# Paths
BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"
OUTPUT_DIR = BASE_DIR / "public"
THEME_DIR = BASE_DIR / "themes" / "default"
ASSETS_DIR = CONTENT_DIR / "assets"
TEMPLATES_DIR = BASE_DIR / "templates"
PLUGINS_DIR = BASE_DIR / "plugins"
WIDGETS_DIR = BASE_DIR / "widgets"
DATA_DIR = BASE_DIR / "data"

# Theme
ACTIVE_THEME = "default"

# Plugins
ACTIVE_PLUGINS = []

# Build Settings
BUILD_MINIFY_HTML = False
BUILD_MINIFY_CSS = False
BUILD_MINIFY_JS = False
BUILD_GENERATE_SITEMAP = True
BUILD_GENERATE_FEED = True
BUILD_CACHE_ENABLED = True
BUILD_PRETTY_URLS = True

# Server (Preview/Serve) - Port 3155
DEV_HOST = "localhost"
DEV_PORT = 3155
DEV_DEBUG = True
DEV_LIVE_RELOAD = True
DEV_OPEN_BROWSER = True

# Studio - Port 3154
STUDIO_ENABLED = True
STUDIO_HOST = "localhost"
STUDIO_PORT = 3154
STUDIO_AUTO_OPEN = True
STUDIO_REQUIRE_LOGIN = True

# Database
DB_ENGINE = "sqlite"
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "root"
DB_PASS = ""
DB_NAME = "metupy_db"
DB_PATH = DATA_DIR / "metupy.db"

# Cache (Redis)
CACHE_ENABLED = True
CACHE_TYPE = "redis"
CACHE_HOST = "localhost"
CACHE_PORT = 6379
CACHE_DB = 0
CACHE_PASSWORD = None
CACHE_TTL = 3600
CACHE_PREFIX = "metupy"

# Security
SECRET_KEY = "dev-secret-key-change-in-production"
TOKEN_EXPIRY = 3600
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CSRF_ENABLED = True
CORS_ENABLED = True
CORS_ORIGINS = ["*"]

# Markdown
MARKDOWN_EXTENSIONS = ["extra", "codehilite", "toc", "tables", "fenced_code"]
MARKDOWN_EXTENSION_CONFIGS = {{}}

# Jinja2
JINJA_EXTENSIONS = ["jinja2.ext.do", "jinja2.ext.loopcontrols"]

# SEO
SEO = {{
    "generate_sitemap": True,
    "generate_robots": True,
    "generate_meta": True,
    "generate_og": True,
    "generate_twitter": True,
}}

# Comments
COMMENTS = {{
    "enabled": True,
    "storage": "redis",
    "sync_time": "00:00",
    "moderation": True,
}}

# Search
SEARCH = {{
    "enabled": True,
    "engine": "lunr",
}}

# Environment
DEBUG = True
TESTING = False
PRODUCTION = False
'''


def create_default_template() -> str:
    """Create default template."""
    return '''<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site.name }}</title>
    <meta name="description" content="{{ metadata.description or site.description }}">
</head>
<body>
    <header>
        <nav>
            <a href="/">{{ site.name }}</a>
            <a href="/blog/">Blog</a>
            <a href="/docs/">Docs</a>
        </nav>
    </header>
    
    <main>
        {{ content | safe }}
    </main>
    
    <footer>
        <p>&copy; {{ now.year }} {{ site.name }}. Built with Metupy.</p>
    </footer>
</body>
</html>
'''


def create_basic_template(project_dir: Path, tree: Tree):
    """Create basic template files."""
    # Create sample page
    page_content = '''# pages/index.py
from metupy.core.page import Page

class IndexPage(Page):
    """Home page"""
    title = "Welcome to Metupy"
    template = "default.html"
    
    def get_context(self):
        return {
            'title': self.title,
            'content': 'Welcome to your new Metupy site!'
        }
'''
    (project_dir / 'pages' / 'index.py').write_text(page_content)
    tree.add('pages/index.py')
    
    # Create sample content
    content = '''---
title: Home
template: default.html
---

# Welcome to Metupy

This is your first page created with Metupy.

## Features

- Markdown support
- Jinja2 templating
- Python integration
- Live reload
'''
    (project_dir / 'content' / 'index.pym').write_text(content)
    tree.add('content/index.pym')


def create_blog_template(project_dir: Path, tree: Tree):
    """Create blog template files."""
    create_basic_template(project_dir, tree)
    
    # Create blog post example
    post_content = '''---
title: My First Post
description: This is my first blog post
date: 2024-01-01
author: Admin
tags: [first, blog]
type: post
template: post.html
---

# My First Post

This is my first blog post created with Metupy.

## Content

Write your blog content here using Markdown.
'''
    (project_dir / 'content' / 'blog' / 'first-post.pym').write_text(post_content)
    tree.add('content/blog/first-post.pym')


def create_docs_template(project_dir: Path, tree: Tree):
    """Create docs template files."""
    create_basic_template(project_dir, tree)
    
    # Create docs example
    docs_content = '''---
title: Getting Started
description: Getting started with Metupy
type: docs
template: docs.html
---

# Getting Started

This guide will help you get started with Metupy.

## Installation

    pip install metupy

## Quick Start

    pym init
    pym serve
'''
    (project_dir / 'content' / 'docs' / 'getting-started.pym').write_text(docs_content)
    tree.add('content/docs/getting-started.pym')


def create_landing_template(project_dir: Path, tree: Tree):
    """Create landing page template files."""
    create_basic_template(project_dir, tree)


def create_slides_template(project_dir: Path, tree: Tree):
    """Create slides template files."""
    create_basic_template(project_dir, tree)


def cmd_new(args):
    """Handle new command."""
    if not args.content_type:
        console.print("[yellow]Please specify content type: page, post, theme, plugin, or widget[/yellow]")
        return
        
    handlers = {
        'page': create_new_page,
        'post': create_new_post,
        'theme': create_new_theme,
        'plugin': create_new_plugin,
        'widget': create_new_widget,
    }
    
    handler = handlers.get(args.content_type)
    if handler:
        handler(args)
    else:
        console.print(f"[red]Unknown content type: {args.content_type}[/red]")


def create_new_page(args):
    """Create new page."""
    page_name = args.name.lower().replace(' ', '_')
    pages_dir = Path('pages')
    pages_dir.mkdir(exist_ok=True)
    
    page_file = pages_dir / f'{page_name}.py'
    
    if page_file.exists():
        console.print(f"[yellow]Page '{page_name}' already exists![/yellow]")
        return
    
    content = f'''# pages/{page_name}.py
from metupy.core.page import Page

class {args.name.replace(' ', '').replace('-', '')}Page(Page):
    """Page description"""
    title = "{args.name}"
    template = "{args.template}.html"
    
    def get_context(self):
        return {{
            'title': self.title,
            'content': 'Page content here'
        }}
'''
    
    page_file.write_text(content)
    console.print(f"[green]✓[/green] Created page: {page_file}")


def create_new_post(args):
    """Create new blog post."""
    from metupy.utils.helpers import slugify
    
    slug = args.slug or slugify(args.title)
    content_dir = Path('content/blog')
    content_dir.mkdir(parents=True, exist_ok=True)
    
    post_file = content_dir / f'{slug}.pym'
    
    if post_file.exists():
        console.print(f"[yellow]Post '{slug}' already exists![/yellow]")
        return
    
    tags = args.tags.split(',') if args.tags else []
    tags_str = str(tags) if tags else '[]'
    author = args.author or 'Admin'
    
    content = f'''---
title: {args.title}
description: 
date: {datetime.now().strftime('%Y-%m-%d')}
author: {author}
tags: {tags_str}
type: post
template: post.html
---

# {args.title}

Write your blog post content here.
'''
    
    post_file.write_text(content)
    console.print(f"[green]✓[/green] Created post: {post_file}")


def create_new_theme(args):
    """Create new theme."""
    theme_name = args.name.lower().replace(' ', '-')
    themes_dir = Path('themes') / theme_name
    themes_dir.mkdir(parents=True, exist_ok=True)
    
    # Create theme.json
    theme_config = {
        "name": theme_name,
        "version": "1.0.0",
        "description": args.description or f"{args.name} theme",
        "author": "Unknown",
    }
    (themes_dir / 'theme.json').write_text(json.dumps(theme_config, indent=2))
    
    # Create templates directory
    templates_dir = themes_dir / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Create default template
    template_content = create_default_template()
    (templates_dir / 'default.html').write_text(template_content)
    
    # Create static directory
    static_dir = themes_dir / 'static'
    static_dir.mkdir(exist_ok=True)
    (static_dir / 'css').mkdir(exist_ok=True)
    (static_dir / 'js').mkdir(exist_ok=True)
    
    console.print(f"[green]✓[/green] Created theme: {theme_name}")


def create_new_plugin(args):
    """Create new plugin."""
    plugin_name = args.name.lower().replace(' ', '-')
    plugin_dir = Path('plugins') / plugin_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create plugin.json
    plugin_config = {
        "name": plugin_name,
        "version": "1.0.0",
        "description": args.description or f"{args.name} plugin",
        "author": "Unknown",
        "dependencies": [],
    }
    (plugin_dir / 'plugin.json').write_text(json.dumps(plugin_config, indent=2))
    
    # Create plugin.py
    plugin_content = f'''from metupy.core.plugin_manager import MetupyPlugin

class {args.name.replace(' ', '').replace('-', '')}Plugin(MetupyPlugin):
    """Plugin description"""
    name = "{plugin_name}"
    version = "1.0.0"
    description = "{args.description or args.name + ' plugin'}"
    author = "Unknown"
    
    def setup(self):
        """Setup plugin"""
        print(f"Plugin {{self.name}} loaded!")
    
    def on_page_after_render(self, page, html):
        """Hook after page render"""
        return html
'''
    (plugin_dir / 'plugin.py').write_text(plugin_content)
    
    console.print(f"[green]✓[/green] Created plugin: {plugin_name}")


def create_new_widget(args):
    """Create new widget."""
    widget_name = args.name.lower().replace(' ', '-')
    widget_file = Path('widgets') / f'{widget_name}.py'
    widget_file.parent.mkdir(parents=True, exist_ok=True)
    
    widget_content = f'''from metupy.core.widget_manager import MetupyWidget

class {args.name.replace(' ', '').replace('-', '')}Widget(MetupyWidget):
    """Widget description"""
    name = "{widget_name}"
    description = "{args.description or args.name + ' widget'}"
    category = "general"
    icon = "📦"
    template = """
<div class="widget widget-{widget_name}" id="{{{{ widget.id }}}}">
    <div class="widget-content">
        {{{{ config.content | safe }}}}
    </div>
</div>"""
    
    settings_schema = {{
        "content": {{
            "type": "textarea",
            "label": "Content",
            "default": "",
        }},
    }}
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        ctx['content'] = self.config.get('content', '')
        return ctx
'''
    
    widget_file.write_text(widget_content)
    console.print(f"[green]✓[/green] Created widget: {widget_name}")


def cmd_clean(args):
    """Handle clean command."""
    clean_output(args.output)
    
    if args.all:
        # Clean cache
        cache_dir = Path('data/cache')
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            console.print("[green]✓[/green] Cleaned cache directory")
        
        # Clean database
        db_file = Path('data/metupy.db')
        if db_file.exists():
            db_file.unlink()
            console.print("[green]✓[/green] Removed database file")


def clean_output(output_dir):
    """Clean output directory."""
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
        output_path.mkdir()
        console.print(f"[green]✓[/green] Cleaned output directory: {output_dir}")
    else:
        console.print(f"[yellow]Output directory '{output_dir}' does not exist[/yellow]")


def cmd_plugin(args):
    """Handle plugin commands."""
    handlers = {
        'list': list_plugins,
        'install': install_plugin,
        'remove': remove_plugin,
        'enable': enable_plugin,
        'disable': disable_plugin,
    }
    
    handler = handlers.get(args.plugin_action)
    if handler:
        handler(args)
    else:
        console.print("[yellow]Please specify action: list, install, remove, enable, or disable[/yellow]")


def list_plugins(args):
    """List installed plugins."""
    plugins_dir = Path('plugins')
    if not plugins_dir.exists():
        console.print("[yellow]No plugins installed[/yellow]")
        return
    
    table = Table(title="Installed Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Status", style="magenta")
    
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir():
            metadata_file = plugin_dir / 'plugin.json'
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                
                # Check if active
                status = "Inactive"
                try:
                    from metupy.config import get_config
                    config = get_config()
                    if metadata['name'] in config.ACTIVE_PLUGINS:
                        status = "Active"
                except:
                    pass
                
                if args.active and status == "Inactive":
                    continue
                    
                table.add_row(
                    metadata.get('name', plugin_dir.name),
                    metadata.get('version', '0.1.0'),
                    metadata.get('description', ''),
                    status,
                )
            else:
                table.add_row(plugin_dir.name, '0.1.0', '', 'Unknown')
    
    console.print(table)


def install_plugin(args):
    """Install plugin."""
    console.print(f"[cyan]Installing plugin: {args.name}[/cyan]")
    console.print(f"[cyan]Source: {args.source}[/cyan]")
    console.print("[yellow]Plugin installation requires internet connection and proper setup[/yellow]")


def remove_plugin(args):
    """Remove plugin."""
    plugin_dir = Path('plugins') / args.name
    if not plugin_dir.exists():
        console.print(f"[yellow]Plugin '{args.name}' not found[/yellow]")
        return
    
    if not args.force:
        if not Confirm.ask(f"Remove plugin '{args.name}'?"):
            return
    
    shutil.rmtree(plugin_dir)
    console.print(f"[green]✓[/green] Removed plugin: {args.name}")


def enable_plugin(args):
    """Enable plugin."""
    console.print(f"[green]✓[/green] Enabled plugin: {args.name}")


def disable_plugin(args):
    """Disable plugin."""
    console.print(f"[green]✓[/green] Disabled plugin: {args.name}")


def cmd_theme(args):
    """Handle theme commands."""
    handlers = {
        'list': list_themes,
        'install': install_theme,
        'create': create_new_theme,
        'activate': activate_theme,
    }
    
    handler = handlers.get(args.theme_action)
    if handler:
        handler(args)
    else:
        console.print("[yellow]Please specify action: list, install, create, or activate[/yellow]")


def list_themes(args):
    """List installed themes."""
    themes_dir = Path('themes')
    if not themes_dir.exists():
        console.print("[yellow]No themes installed[/yellow]")
        return
    
    table = Table(title="Installed Themes")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Status", style="magenta")
    
    for theme_dir in themes_dir.iterdir():
        if theme_dir.is_dir():
            theme_file = theme_dir / 'theme.json'
            if theme_file.exists():
                theme_data = json.loads(theme_file.read_text())
                
                status = "Inactive"
                try:
                    from metupy.config import get_config
                    config = get_config()
                    if theme_data['name'] == config.ACTIVE_THEME:
                        status = "Active"
                except:
                    pass
                
                table.add_row(
                    theme_data.get('name', theme_dir.name),
                    theme_data.get('version', '1.0.0'),
                    theme_data.get('description', ''),
                    status,
                )
    
    console.print(table)


def install_theme(args):
    """Install theme."""
    console.print(f"[cyan]Installing theme: {args.name}[/cyan]")
    console.print("[yellow]Theme installation requires internet connection[/yellow]")


def activate_theme(args):
    """Activate theme."""
    theme_dir = Path('themes') / args.name
    if not theme_dir.exists():
        console.print(f"[yellow]Theme '{args.name}' not found[/yellow]")
        return
    
    # Update pymconfig.py
    config_file = Path('pymconfig.py')
    if config_file.exists():
        content = config_file.read_text()
        import re
        content = re.sub(
            r'ACTIVE_THEME\s*=\s*"[^"]*"',
            f'ACTIVE_THEME = "{args.name}"',
            content
        )
        config_file.write_text(content)
        
    console.print(f"[green]✓[/green] Activated theme: {args.name}")


def cmd_config(args):
    """Handle config commands."""
    handlers = {
        'show': show_config,
        'set': set_config,
    }
    
    handler = handlers.get(args.config_action)
    if handler:
        handler(args)
    else:
        console.print("[yellow]Please specify action: show or set[/yellow]")


def show_config(args):
    """Show configuration."""
    from metupy.config import get_config
    
    config = get_config()
    
    if args.key:
        value = config.get(args.key)
        if value is not None:
            console.print(f"[cyan]{args.key}[/cyan] = [green]{value}[/green]")
        else:
            console.print(f"[yellow]Config key '{args.key}' not found[/yellow]")
    else:
        table = Table(title="Metupy Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.get_all().items():
            if not key.startswith('_'):
                table.add_row(key, str(value))
                
        console.print(table)


def set_config(args):
    """Set configuration value."""
    config_file = Path('pymconfig.py')
    if not config_file.exists():
        console.print("[red]pymconfig.py not found. Run 'pym init' first.[/red]")
        return
    
    content = config_file.read_text()
    
    # Parse value
    value = args.value
    try:
        value = int(value)
    except:
        try:
            value = float(value)
        except:
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.startswith('[') and value.endswith(']'):
                value = value
            else:
                value = f'"{value}"'
    
    import re
    pattern = f'^{args.key}\\s*=.*$'
    replacement = f'{args.key} = {value}'
    
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f'\n{replacement}'
        
    config_file.write_text(content)
    console.print(f"[green]✓[/green] Set {args.key} = {value}")


def cmd_info(args):
    """Show project information."""
    from metupy.config import get_config
    
    console.print(Panel.fit(
        "[bold cyan]Metupy Project Information[/bold cyan]",
        border_style="blue"
    ))
    
    try:
        config = get_config()
        
        table = Table(title="Project Info")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Site Name", str(config.SITE_NAME))
        table.add_row("Site URL", str(config.SITE_URL))
        table.add_row("Site Description", str(config.SITE_DESCRIPTION))
        table.add_row("Site Author", str(config.SITE_AUTHOR))
        table.add_row("Active Theme", str(config.ACTIVE_THEME))
        table.add_row("Active Plugins", str(config.ACTIVE_PLUGINS))
        table.add_row("Output Directory", str(config.OUTPUT_DIR))
        table.add_row("Content Directory", str(config.CONTENT_DIR))
        table.add_row("Studio Port", str(config.STUDIO_PORT))
        table.add_row("Serve Port", str(config.DEV_PORT))
        table.add_row("Environment", "Production" if config.PRODUCTION else "Development")
        
        console.print(table)
        
        # Show content stats
        content_dir = Path(config.CONTENT_DIR)
        if content_dir.exists():
            pym_files = list(content_dir.rglob('*.pym'))
            md_files = list(content_dir.rglob('*.md'))
            
            stats_table = Table(title="Content Statistics")
            stats_table.add_column("Type", style="cyan")
            stats_table.add_column("Count", style="magenta")
            
            stats_table.add_row("PYM Files", str(len(pym_files)))
            stats_table.add_row("Markdown Files", str(len(md_files)))
            stats_table.add_row("Total", str(len(pym_files) + len(md_files)))
            
            console.print(stats_table)
            
    except Exception as e:
        console.print(f"[yellow]Error loading project info: {e}[/yellow]")
        console.print("[yellow]Make sure you're in a Metupy project directory[/yellow]")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route command
    command_handlers = {
        'serve': cmd_serve,
        'build': cmd_build,
        'studio': cmd_studio,
        'init': cmd_init,
        'new': cmd_new,
        'clean': cmd_clean,
        'plugin': cmd_plugin,
        'theme': cmd_theme,
        'config': cmd_config,
        'info': cmd_info,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        parser.print_help()


if __name__ == '__main__':
    main()