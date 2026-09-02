# metupy/core/engine.py
"""Metupy Core Engine - SSG Engine utama."""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, DictLoader
import markdown as md

from metupy.config import get_config


class MetupyEngine:
    """Main Metupy SSG Engine."""
    
    def __init__(self, config_file: str = "pymconfig.py"):
        self.config = get_config()
        
        self.base_dir = getattr(self.config, 'BASE_DIR', Path.cwd())
        self.content_dir = Path(getattr(self.config, 'CONTENT_DIR', self.base_dir / 'content'))
        self.output_dir = Path(getattr(self.config, 'OUTPUT_DIR', self.base_dir / 'public'))
        self.theme_dir = Path(getattr(self.config, 'THEME_DIR', self.base_dir / 'themes' / 'default'))
        self.assets_dir = Path(getattr(self.config, 'ASSETS_DIR', self.content_dir / 'assets'))
        self.templates_dir = Path(getattr(self.config, 'TEMPLATES_DIR', self.base_dir / 'templates'))
        self.plugins_dir = Path(getattr(self.config, 'PLUGINS_DIR', self.base_dir / 'plugins'))
        self.widgets_dir = Path(getattr(self.config, 'WIDGETS_DIR', self.base_dir / 'widgets'))
        self.data_dir = Path(getattr(self.config, 'DATA_DIR', self.base_dir / 'data'))
        
        self.site_context = self._build_site_context()
        
        self.is_building = False
        self.is_serving = False
        self.is_initialized = False
        self.build_stats = {}
        
        self.template_env = None
        self.markdown_parser = None
        self.pym_parser = None
        self.template_parser = None
        self.plugin_manager = None
        self.theme_manager = None
        self.widget_manager = None
        self.content_manager = None
        self.page_manager = None
        self.middleware_manager = None
        self.hook_manager = None
        self.security = None
        self.renderers = {}
        
    def _build_site_context(self) -> Dict[str, Any]:
        return {
            'name': getattr(self.config, 'SITE_NAME', 'Metupy Site'),
            'version': getattr(self.config, 'SITE_VERSION', '1.0.0'),
            'description': getattr(self.config, 'SITE_DESCRIPTION', ''),
            'author': getattr(self.config, 'SITE_AUTHOR', ''),
            'keywords': getattr(self.config, 'SITE_KEYWORDS', []),
            'lang': getattr(self.config, 'SITE_LANG', 'en'),
            'url': getattr(self.config, 'SITE_URL', 'http://localhost:3155'),
        }
        
    def _setup_template_env(self):
        loaders = []
        
        theme_templates = self.theme_dir / 'templates'
        if theme_templates.exists():
            loaders.append(FileSystemLoader(str(theme_templates)))
            
        content_templates = self.content_dir / 'templates'
        if content_templates.exists():
            loaders.append(FileSystemLoader(str(content_templates)))
            
        if self.templates_dir.exists():
            loaders.append(FileSystemLoader(str(self.templates_dir)))
            
        loaders.append(DictLoader({
            'default.html': '''<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site.name }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        header { border-bottom: 1px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 20px; }
        nav a { margin-right: 15px; color: #3b82f6; text-decoration: none; }
        main h1 { font-size: 2em; margin-bottom: 0.5em; }
        main h2 { font-size: 1.5em; margin-top: 1.5em; }
        main ul { padding-left: 20px; }
        footer { border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 40px; color: #6b7280; }
    </style>
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
</html>''',
        }))
        
        env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        def markdown_filter(text):
            if not text:
                return ''
            return md.markdown(text, extensions=['extra', 'tables', 'fenced_code'])
        
        env.filters['markdown'] = markdown_filter
        env.filters['json'] = json.dumps
        
        env.globals['site'] = self.site_context
        env.globals['config'] = self.config.get_all()
        env.globals['now'] = datetime.now()
        env.globals['engine'] = self
        
        self.template_env = env
        
    async def initialize(self):
        if self.is_initialized:
            return
            
        print("Initializing Metupy Engine...")
        
        self._setup_template_env()
        
        try:
            from metupy.core.theme_manager import ThemeManager
            self.theme_manager = ThemeManager(self)
            await self.theme_manager.load_theme()
        except Exception as e:
            print(f"  Warning theme: {e}")
            
        try:
            from metupy.core.content_manager import ContentManager
            self.content_manager = ContentManager(self)
            await self.content_manager.load_content()
        except Exception as e:
            print(f"  Warning content: {e}")
            
        try:
            from metupy.core.page_manager import PageManager
            self.page_manager = PageManager(self)
            await self.page_manager.load_pages()
        except Exception as e:
            print(f"  Warning pages: {e}")
            
        self.is_initialized = True
        print("Metupy Engine initialized successfully")
        
    async def build(self) -> Dict[str, Any]:
        if self.is_building:
            return self.build_stats
            
        if not self.is_initialized:
            await self.initialize()
            
        self.is_building = True
        build_start = datetime.now()
        
        print("\nBuilding Metupy Site...")
        
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        pages_built = 0
        
        if self.content_manager:
            for page in self.content_manager.pages:
                try:
                    template = self.template_env.get_template(page.template)
                    context = page.get_context()
                    if page.content_type in ['pym', 'markdown']:
                        context['content'] = md.markdown(
                            page.content,
                            extensions=['extra', 'tables', 'fenced_code']
                        )
                    html = template.render(**context)
                    output_path = self.output_dir / page.output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(html, encoding='utf-8')
                    pages_built += 1
                    print(f"  Built: {page.title} -> {page.output_path}")
                except Exception as e:
                    print(f"  Error building {page.title}: {e}")
                    
        if self.page_manager:
            for page in self.page_manager.pages:
                try:
                    template = self.template_env.get_template(page.template)
                    context = page.get_context()
                    html = template.render(**context)
                    output_path = self.output_dir / page.output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(html, encoding='utf-8')
                    pages_built += 1
                    print(f"  Built: {page.title} -> {page.output_path}")
                except Exception as e:
                    print(f"  Error building {page.title}: {e}")
                    
        if self.assets_dir.exists():
            shutil.copytree(self.assets_dir, self.output_dir / 'assets', dirs_exist_ok=True)
            
        theme_static = self.theme_dir / 'static'
        if theme_static.exists():
            shutil.copytree(theme_static, self.output_dir, dirs_exist_ok=True)
            
        build_end = datetime.now()
        build_time = (build_end - build_start).total_seconds()
        
        self.build_stats = {
            'pages_built': pages_built,
            'build_time': f"{build_time:.2f}s",
            'output_size': '0 B',
            'timestamp': build_end.isoformat(),
        }
        
        self.is_building = False
        
        print(f"\nBuild completed in {build_time:.2f}s")
        print(f"Pages built: {pages_built}")
        print(f"Output: {self.output_dir}")
        
        return self.build_stats
        
    async def serve(self):
        if not self.is_initialized:
            await self.initialize()
            
        await self.build()
            
        self.is_serving = True
        
        from aiohttp import web
        
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
        
        host = getattr(self.config, 'DEV_HOST', 'localhost')
        port = getattr(self.config, 'DEV_PORT', 3155)
        
        print(f"\nServing site at http://{host}:{port}")
        print("Press Ctrl+C to stop\n")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nServer stopped")
        finally:
            await runner.cleanup()
            self.is_serving = False
        
    async def start_studio(self):
        """Start Metupy Studio CMS."""
        if not self.is_initialized:
            await self.initialize()
            
        from aiohttp import web
        import json as json_module
        
        app = web.Application()
        
        # Studio HTML template
        studio_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metupy Studio</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        * { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen" x-data="studioApp()" x-init="loadData()">
    <!-- Sidebar -->
    <div class="fixed inset-y-0 left-0 w-64 bg-gray-900 text-white">
        <div class="p-6">
            <div class="flex items-center gap-3 mb-8">
                <svg class="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                <div>
                    <h1 class="text-xl font-bold">Metupy</h1>
                    <p class="text-xs text-gray-400">Studio</p>
                </div>
            </div>
            
            <nav class="space-y-2">
                <a href="#" @click.prevent="activeTab='dashboard'" class="flex items-center gap-3 px-4 py-3 rounded-lg transition" :class="activeTab==='dashboard' ? 'bg-blue-600' : 'hover:bg-gray-800'">
                    <span>📊</span> Dashboard
                </a>
                <a href="#" @click.prevent="activeTab='pages'" class="flex items-center gap-3 px-4 py-3 rounded-lg transition" :class="activeTab==='pages' ? 'bg-blue-600' : 'hover:bg-gray-800'">
                    <span>📄</span> Pages
                </a>
                <a href="#" @click.prevent="activeTab='themes'" class="flex items-center gap-3 px-4 py-3 rounded-lg transition" :class="activeTab==='themes' ? 'bg-blue-600' : 'hover:bg-gray-800'">
                    <span>🎨</span> Themes
                </a>
                <a href="#" @click.prevent="activeTab='plugins'" class="flex items-center gap-3 px-4 py-3 rounded-lg transition" :class="activeTab==='plugins' ? 'bg-blue-600' : 'hover:bg-gray-800'">
                    <span>🔌</span> Plugins
                </a>
                <a href="#" @click.prevent="activeTab='widgets'" class="flex items-center gap-3 px-4 py-3 rounded-lg transition" :class="activeTab==='widgets' ? 'bg-blue-600' : 'hover:bg-gray-800'">
                    <span>🧩</span> Widgets
                </a>
                <a href="#" @click.prevent="activeTab='settings'" class="flex items-center gap-3 px-4 py-3 rounded-lg transition" :class="activeTab==='settings' ? 'bg-blue-600' : 'hover:bg-gray-800'">
                    <span>⚙️</span> Settings
                </a>
            </nav>
        </div>
    </div>

    <!-- Main Content -->
    <div class="ml-64 p-8">
        <!-- Top Bar -->
        <div class="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold text-gray-800" x-text="activeTab.charAt(0).toUpperCase() + activeTab.slice(1)"></h1>
                <div class="flex gap-3">
                    <button @click="rebuild()" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">Rebuild Site</button>
                    <a :href="'http://localhost:{{ dev_port }}'" target="_blank" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">View Site</a>
                </div>
            </div>
        </div>

        <!-- Dashboard -->
        <div x-show="activeTab==='dashboard'" class="grid grid-cols-4 gap-6">
            <div class="bg-white rounded-xl p-6 shadow-sm">
                <p class="text-sm text-gray-600">Total Pages</p>
                <p class="text-3xl font-bold text-gray-800" x-text="stats.pages"></p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-sm">
                <p class="text-sm text-gray-600">Total Posts</p>
                <p class="text-3xl font-bold text-gray-800" x-text="stats.posts"></p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-sm">
                <p class="text-sm text-gray-600">Collections</p>
                <p class="text-3xl font-bold text-gray-800" x-text="stats.collections"></p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow-sm">
                <p class="text-sm text-gray-600">Active Theme</p>
                <p class="text-xl font-bold text-gray-800" x-text="stats.theme"></p>
            </div>
        </div>

        <!-- Pages -->
        <div x-show="activeTab==='pages'" class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="font-semibold mb-4">All Pages</h3>
            <table class="w-full">
                <thead>
                    <tr class="border-b">
                        <th class="text-left py-2">Title</th>
                        <th class="text-left py-2">Type</th>
                        <th class="text-left py-2">URL</th>
                    </tr>
                </thead>
                <tbody>
                    <template x-for="page in pages" :key="page.id">
                        <tr class="border-b">
                            <td class="py-2" x-text="page.title"></td>
                            <td class="py-2" x-text="page.type"></td>
                            <td class="py-2" x-text="page.url"></td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>

        <!-- Themes -->
        <div x-show="activeTab==='themes'" class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="font-semibold mb-4">Themes</h3>
            <p>Active theme: <span x-text="stats.theme"></span></p>
        </div>

        <!-- Plugins -->
        <div x-show="activeTab==='plugins'" class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="font-semibold mb-4">Plugins</h3>
            <p>No plugins active.</p>
        </div>

        <!-- Widgets -->
        <div x-show="activeTab==='widgets'" class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="font-semibold mb-4">Widgets</h3>
            <p>No widgets registered.</p>
        </div>

        <!-- Settings -->
        <div x-show="activeTab==='settings'" class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="font-semibold mb-4">Site Settings</h3>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Site Name</label>
                    <input type="text" class="w-full px-3 py-2 border rounded-lg" :value="siteConfig.name">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Site URL</label>
                    <input type="text" class="w-full px-3 py-2 border rounded-lg" :value="siteConfig.url">
                </div>
            </div>
        </div>
    </div>

    <script>
        function studioApp() {
            return {
                activeTab: 'dashboard',
                stats: { pages: 0, posts: 0, collections: 0, theme: 'default' },
                pages: [],
                siteConfig: { name: '', url: '' },
                
                async loadData() {
                    try {
                        const res = await fetch('/api/stats');
                        const data = await res.json();
                        this.stats = data;
                        this.siteConfig.name = data.site_name;
                        this.siteConfig.url = data.site_url;
                        
                        const pagesRes = await fetch('/api/pages');
                        const pagesData = await pagesRes.json();
                        this.pages = pagesData;
                    } catch (e) {
                        console.error('Error loading data:', e);
                    }
                },
                
                async rebuild() {
                    try {
                        await fetch('/api/rebuild', { method: 'POST' });
                        alert('Site rebuilt!');
                    } catch (e) {
                        alert('Rebuild failed');
                    }
                }
            }
        }
    </script>
</body>
</html>'''
        
        studio_html = studio_html.replace('{{ dev_port }}', str(getattr(self.config, 'DEV_PORT', 3155)))
        
        async def index(request):
            return web.Response(text=studio_html, content_type='text/html')
            
        async def api_stats(request):
            stats = {
                'pages': len(self.content_manager.pages) if self.content_manager else 0,
                'posts': len(self.content_manager.posts) if self.content_manager else 0,
                'collections': len(self.content_manager.collections) if self.content_manager else 0,
                'theme': getattr(self.config, 'ACTIVE_THEME', 'default'),
                'site_name': getattr(self.config, 'SITE_NAME', 'Metupy Site'),
                'site_url': getattr(self.config, 'SITE_URL', 'http://localhost:3155'),
            }
            return web.json_response(stats)
            
        async def api_pages(request):
            pages = []
            if self.content_manager:
                for p in self.content_manager.pages:
                    pages.append({
                        'id': p.id,
                        'title': p.title,
                        'type': p.content_type,
                        'url': p.url,
                    })
            if self.page_manager:
                for p in self.page_manager.pages:
                    pages.append({
                        'id': p.id,
                        'title': p.title,
                        'type': 'python',
                        'url': p.url,
                    })
            return web.json_response(pages)
            
        async def api_rebuild(request):
            await self.build()
            return web.json_response({'success': True})
            
        app.router.add_get('/', index)
        app.router.add_get('/api/stats', api_stats)
        app.router.add_get('/api/pages', api_pages)
        app.router.add_post('/api/rebuild', api_rebuild)
        
        host = getattr(self.config, 'STUDIO_HOST', 'localhost')
        port = getattr(self.config, 'STUDIO_PORT', 3154)
        
        print(f"\nStudio running at http://{host}:{port}")
        print("Press Ctrl+C to stop\n")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nStudio stopped")
        finally:
            await runner.cleanup()