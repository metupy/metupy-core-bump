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
        self.config = get_config(config_file if config_file != "pymconfig.py" else None)

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
        """Find the active theme in project, user, or installed package paths."""
        active_theme = getattr(self.config, 'ACTIVE_THEME', None) or 'peradocs'
        theme_name = Path(str(active_theme)).expanduser()

        if theme_name.is_absolute():
            candidates = [theme_name]
        else:
            candidates = [
                self.base_dir / 'themes' / theme_name,
                Path.home() / '.metupy' / 'themes' / theme_name,
            ]
            try:
                import metupy
                candidates.append(
                    Path(metupy.__file__).resolve().parent / 'themes' / theme_name
                )
            except (ImportError, AttributeError):
                pass

        # A theme only needs templates; static assets are optional.
        for candidate in candidates:
            if candidate.is_dir() and (candidate / 'templates').is_dir():
                return candidate
        # Keep a useful deterministic path if the configured theme is missing.
        return candidates[0]


    def _build_site_context(self) -> Dict[str, Any]:
        """Build site-wide context for templates."""
        return {
            'name': getattr(self.config, 'SITE_NAME', None) or 'Metupy Site',
            'title': getattr(self.config, 'SITE_NAME', None) or 'Metupy Site',
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

        # Fallback templates (always available)
        loaders.append(DictLoader({
            'base.html': '''<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site.name }}</title>
    <link rel="icon" type="image/png" href="/favicon.png?v={{ site.version }}">
    <link rel="stylesheet" href="/peradocs.css">
    <link rel="stylesheet" href="/header.css">
    <link rel="stylesheet" href="/sidebar.css">
    <link rel="stylesheet" href="/toc.css">
    <link rel="stylesheet" href="/content.css">
    <link rel="stylesheet" href="/search.css">
    <link rel="stylesheet" href="/footer.css">
    <link rel="stylesheet" href="/responsive.css">
    <link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">
</head>
<body>
    {% include "_partials/_header.html" %}
    {% block content %}{% endblock %}
    {% include "_partials/_search_modal.html" %}
    <script src="/peradocs.js"></script>
    <script src="/header.js"></script>
    <script src="/sidebar.js"></script>
    <script src="/toc.js"></script>
    <script src="/search.js"></script>
</body>
</html>''',
            'layout.html': '''{% extends "base.html" %}
{% block content %}
<div class="metu-docs-layout">
    {% include "_partials/_sidebar.html" %}
    <main class="metu-docs-content">
        <h1>{{ title }}</h1>
        {% if metadata.description %}<p class="metu-lead">{{ metadata.description }}</p>{% endif %}
        {{ content | safe }}
        {% include "_partials/_edit_this_page.html" %}
        {% if prev_doc or next_doc %}
        <div class="metu-doc-footer-nav">
            {% if prev_doc %}<a href="{{ prev_doc.url }}" class="metu-nav-card metu-prev-card"><span class="metu-nav-label"><i class="bx bx-chevron-left"></i> Previous</span><span class="metu-nav-title">{{ prev_doc.title }}</span></a>{% endif %}
            {% if next_doc %}<a href="{{ next_doc.url }}" class="metu-nav-card metu-next-card"><span class="metu-nav-label">Next <i class="bx bx-chevron-right"></i></span><span class="metu-nav-title">{{ next_doc.title }}</span></a>{% endif %}
        </div>
        {% endif %}
    </main>
    {% include "_partials/_toc.html" %}
</div>
{% include "_partials/_footer.html" %}
{% endblock %}''',
            '_partials/_header.html': '''<header><div class="metu-header-container"><div class="metu-brand"><a href="/"><span>{{ site.name }}</span></a></div></div></header>''',
            '_partials/_sidebar.html': '''<aside class="metu-docs-sidebar"><ul>{% for group in sidebar_groups %}<li>{{ group.title }}<ul>{% for item in group['items'] %}<li><a href="{{ item.url }}" class="{% if item.current %}metu-active{% endif %}">{{ item.title }}</a></li>{% endfor %}</ul></li>{% endfor %}</ul></aside>''',
            '_partials/_toc.html': '''<aside class="metu-docs-toc"><nav>{% for item in toc_items %}<a href="#{{ item.anchor }}">{{ item.title }}</a>{% endfor %}</nav></aside>''',
            '_partials/_search_modal.html': '',
            '_partials/_edit_this_page.html': '',
            '_partials/_footer.html': '<footer>Built with Metupy - {{ config.ACTIVE_THEME }}</footer>',
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

        try:
            from metupy.core.content_manager import ContentManager
            self.content_manager = ContentManager(self)
            await self.content_manager.load_content()
        except Exception as e:
            print(f"Warning: Content manager failed: {e}")
            self.content_manager = None

        try:
            from metupy.core.page_manager import PageManager
            self.page_manager = PageManager(self)
            await self.page_manager.load_pages()
        except Exception:
            self.page_manager = None

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

        if not self.template_env:
            self._setup_template_env()

        self.is_building = True
        build_start = datetime.now()

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        pages_built = 0

        # Footer integrity check for production
        production = getattr(self.config, 'PRODUCTION', False)
        if production and not self._check_footer_integrity():
            error_html = """<!DOCTYPE html>
<html lang="en">
<head><title>Footer Locked</title></head>
<body><h1>Footer credit is locked</h1><p>The Metupy footer credit cannot be modified.</p></body>
</html>"""
            (self.output_dir / 'index.html').write_text(error_html, encoding='utf-8')
            self.is_building = False
            return {'pages_built': 1, 'build_time': '0.00s', 'footer_locked': True}

        # Build content pages
        if self.content_manager:
            for page in self.content_manager.pages:
                try:
                    template = self.template_env.get_template(page.template) # type: ignore
                    context = page.get_context()

                    if page.content_type == 'pym':
                        content_template = self.template_env.from_string(page.content) # type: ignore
                        rendered_content = content_template.render(**context)
                        context['content'] = md.markdown(
                            rendered_content,
                            extensions=['extra', 'tables', 'fenced_code']
                        )
                    elif page.content_type == 'markdown':
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

                        repo_url = getattr(self.config, 'GH_REPO_URL', '')
                        if repo_url and page.source_file:
                            relative = page.source_file.relative_to(self.base_dir)
                            context['edit_url'] = f"{repo_url.rstrip('/')}/blob/main/{relative.as_posix()}"

                    html = template.render(**context)
                    output_path = self.output_dir / page.output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(html, encoding='utf-8')
                    pages_built += 1
                except Exception as e:
                    if verbose:
                        print(f"  Error building {page.title}: {e}")

        # Build Python pages
        if self.page_manager:
            for page in self.page_manager.pages:
                try:
                    template = self.template_env.get_template(page.template) # type: ignore
                    context = page.get_context()
                    html = template.render(**context)
                    output_path = self.output_dir / page.output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(html, encoding='utf-8')
                    pages_built += 1
                except Exception as e:
                    if verbose:
                        print(f"  Error building {page.title}: {e}")

        # Copy theme static files to output root
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

        # Copy assets if present
        assets_dir = getattr(self.config, 'ASSETS_DIR', None)
        if assets_dir:
            assets_path = Path(assets_dir)
            if assets_path.exists():
                shutil.copytree(assets_path, self.output_dir / 'assets', dirs_exist_ok=True)

        # Copy the active theme favicon to the project root when needed.
        project_favicon = self.base_dir / 'favicon.png'
        theme_favicon = self.theme_dir / 'favicon.png'
        if not theme_favicon.exists():
            try:
                import metupy
                bundled_favicon = (
                    Path(metupy.__file__).resolve().parent
                    / 'themes' / getattr(self.config, 'ACTIVE_THEME', 'peradocs')
                    / 'favicon.png'
                )
                if bundled_favicon.exists():
                    theme_favicon = bundled_favicon
            except (ImportError, AttributeError):
                pass

        if theme_favicon.exists():
            shutil.copy2(theme_favicon, project_favicon)

        # Copy favicon from the project root to the build output.
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

        self.is_serving = True

        from aiohttp import web
        import signal
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        app = web.Application()
        loop = asyncio.get_running_loop()
        reload_clients = set()
        reload_task = None
        observer = Observer()

        async def notify_reload() -> None:
            """Rebuild the site and tell connected browsers to reload."""
            await asyncio.sleep(0.2)
            if self.content_manager:
                await self.content_manager.reload()
            if self.page_manager:
                await self.page_manager.reload()
            await self.build(verbose=verbose)
            for websocket in list(reload_clients):
                if not websocket.closed:
                    await websocket.send_json({'type': 'reload'})

        def schedule_reload() -> None:
            nonlocal reload_task
            if reload_task is None or reload_task.done():
                reload_task = asyncio.create_task(notify_reload())

        class ChangeHandler(FileSystemEventHandler):
            def on_any_event(self, event) -> None:
                if not event.is_directory:
                    loop.call_soon_threadsafe(schedule_reload)

        async def reload_socket(request):
            websocket = web.WebSocketResponse()
            await websocket.prepare(request)
            reload_clients.add(websocket)
            await websocket.send_json({'type': 'connected'})
            try:
                async for _ in websocket:
                    pass
            except asyncio.CancelledError:
                pass
            finally:
                reload_clients.discard(websocket)
                if not websocket.closed:
                    await websocket.close()
            return websocket

        reload_script = """<script>
(function () {
  var socket;
  function connect() {
    socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/__metupy_reload');
    socket.onmessage = function (event) {
      if (JSON.parse(event.data).type === 'reload') location.reload();
    };
    socket.onclose = function () { setTimeout(connect, 500); };
  }
  connect();
}());
</script>"""

        def html_response(file_path: Path):
            html = file_path.read_text(encoding='utf-8')
            if '</body>' in html:
                html = html.replace('</body>', reload_script + '</body>', 1)
            else:
                html += reload_script
            return web.Response(text=html, content_type='text/html')

        async def handle(request):
            path = request.path.lstrip('/')
            if not path:
                path = 'index.html'
            file_path = self.output_dir / path
            if file_path.exists() and file_path.is_file():
                if file_path.suffix.lower() == '.html':
                    return html_response(file_path)
                if file_path.name == 'favicon.png':
                    return web.FileResponse(
                        file_path,
                        headers={'Cache-Control': 'no-store, max-age=0'},
                    )
                return web.FileResponse(file_path)
            index_path = file_path / 'index.html'
            if index_path.exists():
                return html_response(index_path)
            return web.Response(text="404 Not Found", status=404)

        app.router.add_get('/__metupy_reload', reload_socket)
        app.router.add_get('/{path:.*}', handle)

        host = getattr(self.config, 'DEV_HOST', None) or 'localhost'
        port = getattr(self.config, 'DEV_PORT', None) or 3155

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        handler = ChangeHandler()
        watch_dirs = [
            self.content_dir,
            self.theme_dir,
            self.base_dir / 'pages',
            self.base_dir / 'plugins',
        ]
        for directory in watch_dirs:
            if directory.exists():
                observer.schedule(handler, str(directory), recursive=True)
        observer.start()

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
        except asyncio.CancelledError:
            pass
        finally:
            if reload_task and not reload_task.done():
                reload_task.cancel()
                await asyncio.gather(reload_task, return_exceptions=True)
            if reload_clients:
                await asyncio.gather(
                    *(websocket.close() for websocket in list(reload_clients)),
                    return_exceptions=True,
                )
            observer.stop()
            observer.join()
            await runner.shutdown()
            await runner.cleanup()
            self.is_serving = False

    async def start_studio(self) -> None:
        """Start Metupy Studio CMS."""
        if not self.is_initialized:
            await self.initialize()

        from aiohttp import web
        import signal

        app = web.Application()

        async def index(request):
            return web.Response(text="<h1>Metupy Studio</h1>", content_type='text/html')

        app.router.add_get('/', index)

        host = getattr(self.config, 'STUDIO_HOST', None) or 'localhost'
        port = getattr(self.config, 'STUDIO_PORT', None) or 3154

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