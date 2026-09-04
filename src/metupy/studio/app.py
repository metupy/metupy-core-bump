"""
Studio application for Metupy.

Provides CMS web interface for managing Metupy content.
"""

import asyncio
import signal
from typing import Any, Dict

from aiohttp import web


class StudioApp:
    """Metupy Studio CMS application."""

    def __init__(self, engine):
        """
        Initialize StudioApp.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup Studio routes."""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/api/stats', self.api_stats)
        self.app.router.add_get('/api/pages', self.api_pages)
        self.app.router.add_post('/api/rebuild', self.api_rebuild)

    async def index(self, request) -> web.Response:
        """
        Serve Studio HTML interface.

        Args:
            request: Aiohttp request.

        Returns:
            HTML response.
        """
        studio_html = self._get_studio_html()
        return web.Response(text=studio_html, content_type='text/html')

    async def api_stats(self, request) -> web.Response:
        """
        Return site statistics.

        Args:
            request: Aiohttp request.

        Returns:
            JSON response.
        """
        content_manager = getattr(self.engine, 'content_manager', None)
        page_manager = getattr(self.engine, 'page_manager', None)

        return web.json_response({
            'pages': len(content_manager.pages) if content_manager else 0,
            'python_pages': len(page_manager.pages) if page_manager else 0,
            'posts': len(content_manager.posts) if content_manager else 0,
            'theme': getattr(self.engine.config, 'ACTIVE_THEME', 'default'),
            'site_name': getattr(self.engine.config, 'SITE_NAME', 'Metupy Site'),
        })

    async def api_pages(self, request) -> web.Response:
        """
        Return list of all pages.

        Args:
            request: Aiohttp request.

        Returns:
            JSON response with pages.
        """
        pages = []

        content_manager = getattr(self.engine, 'content_manager', None)
        page_manager = getattr(self.engine, 'page_manager', None)

        if content_manager:
            for p in content_manager.pages:
                pages.append({
                    'id': p.id,
                    'title': p.title,
                    'url': p.url,
                    'type': p.content_type,
                })

        if page_manager:
            for p in page_manager.pages:
                pages.append({
                    'id': p.id,
                    'title': p.title,
                    'url': p.url,
                    'type': 'python',
                })

        return web.json_response(pages)

    async def api_rebuild(self, request) -> web.Response:
        """
        Trigger site rebuild.

        Args:
            request: Aiohttp request.

        Returns:
            JSON response.
        """
        await self.engine.build()
        return web.json_response({'success': True})

    def _get_studio_html(self) -> str:
        """
        Generate Studio HTML interface.

        Returns:
            HTML string.
        """
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metupy Studio</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-50 min-h-screen" x-data="studioApp()" x-init="loadData()">
    <div class="fixed inset-y-0 left-0 w-64 bg-gray-900 text-white">
        <div class="p-6">
            <h1 class="text-xl font-bold mb-8">Metupy Studio</h1>
            <nav class="space-y-2">
                <a href="#" @click.prevent="activeTab='dashboard'" class="block px-4 py-2 rounded" :class="activeTab==='dashboard' ? 'bg-blue-600' : 'hover:bg-gray-800'">Dashboard</a>
                <a href="#" @click.prevent="activeTab='pages'" class="block px-4 py-2 rounded" :class="activeTab==='pages' ? 'bg-blue-600' : 'hover:bg-gray-800'">Pages</a>
                <a href="#" @click.prevent="activeTab='settings'" class="block px-4 py-2 rounded" :class="activeTab==='settings' ? 'bg-blue-600' : 'hover:bg-gray-800'">Settings</a>
            </nav>
        </div>
    </div>
    <div class="ml-64 p-8">
        <h1 class="text-2xl font-bold mb-6" x-text="activeTab.charAt(0).toUpperCase() + activeTab.slice(1)"></h1>
        <div x-show="activeTab==='dashboard'" class="grid grid-cols-3 gap-6">
            <div class="bg-white rounded-xl p-6 shadow">
                <p class="text-sm text-gray-600">Pages</p>
                <p class="text-3xl font-bold" x-text="stats.pages + stats.python_pages"></p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow">
                <p class="text-sm text-gray-600">Posts</p>
                <p class="text-3xl font-bold" x-text="stats.posts"></p>
            </div>
            <div class="bg-white rounded-xl p-6 shadow">
                <p class="text-sm text-gray-600">Theme</p>
                <p class="text-xl font-bold" x-text="stats.theme"></p>
            </div>
        </div>
        <div x-show="activeTab==='pages'" class="bg-white rounded-xl shadow p-6">
            <table class="w-full">
                <thead><tr class="border-b"><th class="text-left py-2">Title</th><th class="text-left py-2">Type</th><th class="text-left py-2">URL</th></tr></thead>
                <tbody>
                    <template x-for="p in pages" :key="p.id">
                        <tr class="border-b"><td class="py-2" x-text="p.title"></td><td class="py-2" x-text="p.type"></td><td class="py-2" x-text="p.url"></td></tr>
                    </template>
                </tbody>
            </table>
        </div>
        <div x-show="activeTab==='settings'" class="bg-white rounded-xl shadow p-6">
            <button @click="rebuild()" class="px-4 py-2 bg-green-600 text-white rounded">Rebuild Site</button>
        </div>
    </div>
    <script>
        function studioApp() {
            return {
                activeTab: 'dashboard',
                stats: { pages: 0, python_pages: 0, posts: 0, theme: 'default' },
                pages: [],
                async loadData() {
                    const res = await fetch('/api/stats');
                    this.stats = await res.json();
                    const pagesRes = await fetch('/api/pages');
                    this.pages = await pagesRes.json();
                },
                async rebuild() {
                    await fetch('/api/rebuild', { method: 'POST' });
                    alert('Rebuilt!');
                }
            }
        }
    </script>
</body>
</html>'''

    async def start(self) -> None:
        """
        Start Studio server.

        Blocks until Ctrl+C is pressed.
        """
        host = getattr(self.engine.config, 'STUDIO_HOST', 'localhost')
        port = getattr(self.engine.config, 'STUDIO_PORT', 3154)

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        print(f"\nStudio running at http://{host}:{port}")
        print("Press Ctrl+C to stop\n")

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
            print("Studio stopped")