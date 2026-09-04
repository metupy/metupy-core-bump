"""
Core engine for Metupy SSG.

Provides the main MetupyEngine class that orchestrates all
components including content loading, building, and serving.
"""

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import markdown as md
from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader

from metupy.config import get_config


class MetupyEngine:
    """Main Metupy SSG Engine."""

    def __init__(self, config_file: str = "pymconfig.py"):
        """
        Initialize MetupyEngine.

        Args:
            config_file: Configuration file name. Defaults to "pymconfig.py".
        """
        self.config = get_config()

        base_dir = getattr(self.config, 'BASE_DIR', None)
        if base_dir is None:
            base_dir = Path.cwd()
        self.base_dir = Path(base_dir)

        content_dir = getattr(self.config, 'CONTENT_DIR', None)
        if content_dir is None:
            content_dir = self.base_dir / 'docs'
        self.content_dir = Path(content_dir)

        output_dir = getattr(self.config, 'OUTPUT_DIR', None)
        if output_dir is None:
            output_dir = Path.home() / '.metupy' / 'output' / self.base_dir.name
        self.output_dir = Path(output_dir)

        theme_dir = getattr(self.config, 'THEME_DIR', None)
        if theme_dir is None:
            theme_dir = self._find_theme_dir()
        self.theme_dir = Path(theme_dir)

        self.site_context = self._build_site_context()

        self.is_building = False
        self.is_serving = False
        self.is_initialized = False
        self.build_stats: Dict[str, Any] = {}

        self.template_env: Optional[Environment] = None
        self.security = None
        self.content_manager = None
        self.page_manager = None
        self.navigation = []

    def _find_theme_dir(self) -> Path:
        """Find theme directory. Search package, user, project."""
        active_theme = getattr(self.config, 'ACTIVE_THEME', None) or 'peradocs'

        try:
            import metupy
            package_dir = Path(metupy.__file__).parent
            bundled = package_dir / 'themes' / active_theme
            if bundled.exists() and (bundled / 'templates').exists():
                return bundled
        except (ImportError, AttributeError):
            pass

        user_theme = Path.home() / '.metupy' / 'themes' / active_theme
        if user_theme.exists() and (user_theme / 'templates').exists():
            return user_theme

        project_theme = self.base_dir / 'themes' / active_theme
        return project_theme

    def _build_site_context(self) -> Dict[str, Any]:
        """Build site-wide context for templates."""
        return {
            'name': getattr(self.config, 'SITE_NAME', None) or 'Metupy Site',
            'version': getattr(self.config, 'SITE_VERSION', None) or '1.0.0',
            'description': getattr(self.config, 'SITE_DESCRIPTION', None) or '',
            'author': getattr(self.config, 'SITE_AUTHOR', None) or '',
            'keywords': getattr(self.config, 'SITE_KEYWORDS', None) or [],
            'lang': getattr(self.config, 'SITE_LANG', None) or 'en',
            'url': getattr(self.config, 'SITE_URL', None) or 'http://localhost:3155',
        }

    def _setup_template_env(self) -> None:
        """Initialize Jinja2 template environment."""
        loaders = []

        theme_templates = self.theme_dir / 'templates'
        if theme_templates.exists():
            loaders.append(FileSystemLoader(str(theme_templates)))
            partials_dir = theme_templates / '_partials'
            if partials_dir.exists():
                loaders.append(FileSystemLoader(str(partials_dir)))

        # Fallback templates
        loaders.append(DictLoader({
            'base.html': '''<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site.name }}</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 2em; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { font-family: monospace; }
        footer { border-top: 1px solid #eee; margin-top: 40px; padding-top: 20px; text-align: center; color: #666; }
    </style>
</head>
<body>
    <header><h1>{{ site.name }}</h1></header>
    <main>{{ content | safe }}</main>
    <footer><p>Built with Metupy - {{ config.ACTIVE_THEME }}</p></footer>
</body>
</html>''',
            'layout.html': '''{% extends "base.html" %}
{% block content %}
<main>
    <h1>{{ title }}</h1>
    {{ content | safe }}
</main>
{% endblock %}''',
        }))

        env = Environment(
            loader=ChoiceLoader(loaders),
            extensions=getattr(self.config, 'JINJA_EXTENSIONS', None) or [],
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        def markdown_filter(text: str) -> str:
            if not text:
                return ''
            return md.markdown(text, extensions=['extra', 'tables', 'fenced_code'])

        env.filters['markdown'] = markdown_filter
        env.filters['json'] = json.dumps

        env.globals['site'] = self.site_context
        env.globals['config'] = self.config.get_all() if self.config else {}
        env.globals['now'] = datetime.now()
        env.globals['engine'] = self

        self.template_env = env

    async def initialize(self) -> None:
        """Initialize engine components."""
        if self.is_initialized:
            return

        self._setup_template_env()

        from metupy.core.content_manager import ContentManager
        self.content_manager = ContentManager(self)
        await self.content_manager.load_content()

        self.is_initialized = True

    def _check_footer_integrity(self) -> bool:
        """
        Verify that the footer contains the locked credit text.
        Returns True if footer is unchanged.
        """
        footer_file = self.theme_dir / 'templates' / '_partials' / '_footer.html'
        if footer_file.exists():
            content = footer_file.read_text(encoding='utf-8')
        else:
            # Fallback: base template footer
            base_file = self.theme_dir / 'templates' / 'base.html'
            if base_file.exists():
                content = base_file.read_text(encoding='utf-8')
            else:
                return False

        expected_theme = getattr(self.config, 'ACTIVE_THEME', 'peradocs')
        expected = f"Built with Metupy - {expected_theme}"
        return expected in content

    async def build(self, verbose: bool = False) -> Dict[str, Any]:
        """Build static site."""
        if self.is_building:
            return self.build_stats

        if not self.is_initialized:
            await self.initialize()

        self.is_building = True
        build_start = datetime.now()

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        pages_built = 0

        # Footer integrity check for production
        production = getattr(self.config, 'PRODUCTION', False)
        if production and not self._check_footer_integrity():
            # Render full page lock error
            error_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Footer Locked</title>
    <style>
        body { font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #fef2f2; }
        .box { text-align: center; padding: 3rem; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,.1); }
        h1 { color: #dc2626; }
        p { color: #4b5563; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Footer credit is locked</h1>
        <p>The Metupy footer credit cannot be modified. Please restore the original footer to proceed.</p>
    </div>
</body>
</html>"""
            (self.output_dir / 'index.html').write_text(error_html, encoding='utf-8')
            self.is_building = False
            return {'pages_built': 1, 'build_time': '0.00s', 'footer_locked': True}

        for page in self.content_manager.pages:
            try:
                template = self.template_env.get_template(page.template)
                context = page.get_context()

                if page.content_type in ['pym', 'markdown']:
                    context['content'] = md.markdown(
                        page.content,
                        extensions=['extra', 'tables', 'fenced_code']
                    )

                if page.metadata.get('type') == 'docs':
                    context['sidebar_groups'] = self.content_manager.get_docs_sidebar(page)
                    context['toc_items'] = self.content_manager.get_toc_items(page)
                    prev_doc, next_doc = self.content_manager.get_prev_next_docs(page)
                    context['prev_doc'] = {'title': prev_doc.title, 'url': prev_doc.url} if prev_doc else None
                    context['next_doc'] = {'title': next_doc.title, 'url': next_doc.url} if next_doc else None

                html = template.render(**context)
                output_path = self.output_dir / page.output_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(html, encoding='utf-8')
                pages_built += 1
            except Exception as e:
                if verbose:
                    print(f"  Error building {page.title}: {e}")

        # Copy theme static files
        theme_static = self.theme_dir / 'static'
        if theme_static.exists():
            for item in theme_static.iterdir():
                if item.is_dir():
                    for subitem in item.iterdir():
                        dest = self.output_dir / subitem.name
                        if subitem.is_dir():
                            shutil.copytree(subitem, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(subitem, dest)
                else:
                    shutil.copy2(item, self.output_dir / item.name)

        # Copy favicon
        project_favicon = self.base_dir / 'favicon.png'
        if project_favicon.exists():
            shutil.copy2(project_favicon, self.output_dir / 'favicon.png')

        build_end = datetime.now()
        self.build_stats = {
            'pages_built': pages_built,
            'build_time': f"{(build_end - build_start).total_seconds():.2f}s",
            'output_size': self._get_directory_size(),
            'timestamp': build_end.isoformat(),
        }

        self.is_building = False
        return self.build_stats

    def _get_directory_size(self) -> str:
        if not self.output_dir.exists():
            return "0 B"
        total = sum(f.stat().st_size for f in self.output_dir.rglob('*') if f.is_file())
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total < 1024:
                return f"{total:.2f} {unit}"
            total /= 1024
        return f"{total:.2f} TB"

    async def serve(self, verbose: bool = False) -> None:
        """Serve site with development server."""
        if not self.is_initialized:
            await self.initialize()

        await self.build(verbose=verbose)

        from aiohttp import web
        import signal

        app = web.Application()

        async def handle(request):
            path = request.path.lstrip('/')
            if not path:
                path = 'index.html'
            file_path = self.output_dir / path
            if file_path.exists() and file_path.is_file():
                return web.FileResponse(file_path)
            index_path = file_path / 'index.html'
            if index_path.exists():
                return web.FileResponse(index_path)
            return web.Response(text="404 Not Found", status=404)

        app.router.add_get('/{path:.*}', handle)

        host = getattr(self.config, 'DEV_HOST', None) or 'localhost'
        port = getattr(self.config, 'DEV_PORT', None) or 3155

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()

        def signal_handler():
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                pass

        try:
            await stop_event.wait()
        finally:
            await runner.cleanup()