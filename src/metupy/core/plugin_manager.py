"""
Plugin manager for Metupy.

Provides plugin registration, loading, and hook execution
for extending Metupy functionality.
"""

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from metupy.core.hooks import HookManager


class MetupyPlugin:
    """Base class for all Metupy plugins."""

    name: str = "base-plugin"
    version: str = "1.0.0"
    description: str = "Base plugin"
    author: str = "Unknown"
    url: str = ""
    dependencies: List[str] = []

    def __init__(self, engine):
        """
        Initialize plugin.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.config = getattr(engine, 'config', None)

    def setup(self) -> None:
        """Setup plugin. Override in subclasses."""
        pass

    def on_init(self, engine) -> None:
        """Hook called when engine initializes."""
        pass

    def on_build_start(self, engine) -> None:
        """Hook called when build starts."""
        pass

    def on_build_end(self, engine) -> None:
        """Hook called when build ends."""
        pass

    def on_page_before_render(self, page, context: Dict) -> Dict:
        """
        Hook called before page render.

        Args:
            page: Page being rendered.
            context: Rendering context.

        Returns:
            Modified context.
        """
        return context

    def on_page_after_render(self, page, html: str) -> str:
        """
        Hook called after page render.

        Args:
            page: Page that was rendered.
            html: Rendered HTML.

        Returns:
            Modified HTML.
        """
        return html

    def register_filters(self, env) -> None:
        """Register custom Jinja2 filters."""
        pass

    def register_globals(self, env) -> None:
        """Register custom Jinja2 globals."""
        pass

    def setup_routes(self, app) -> None:
        """Setup API routes for plugin."""
        pass

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class PluginManager:
    """Manage Metupy plugins."""

    def __init__(self, engine):
        """
        Initialize PluginManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.plugins: Dict[str, MetupyPlugin] = {}
        self.active_plugins: List[MetupyPlugin] = []
        self.plugin_hooks: Dict[str, List[Callable]] = {}

    async def load_plugins(self) -> None:
        """Load all plugins."""
        self._load_builtin_plugins()
        await self._load_user_plugins()
        await self._initialize_plugins()
        self._register_hooks()

    def _load_builtin_plugins(self) -> None:
        """Load built-in plugins."""
        builtin_plugins = []

        try:
            from metupy.plugins.seo import SEOPlugin
            builtin_plugins.append(SEOPlugin)
        except ImportError:
            pass

        try:
            from metupy.plugins.sitemap import SitemapPlugin
            builtin_plugins.append(SitemapPlugin)
        except ImportError:
            pass

        try:
            from metupy.plugins.comments import CommentsPlugin
            builtin_plugins.append(CommentsPlugin)
        except ImportError:
            pass

        for plugin_class in builtin_plugins:
            try:
                plugin = plugin_class(self.engine)
                self.plugins[plugin.name] = plugin
            except Exception as e:
                print(f"  Plugin load error: {e}")

    async def _load_user_plugins(self) -> None:
        """Load user plugins from plugins directory."""
        plugins_dir = Path(getattr(self.engine.config, 'PLUGINS_DIR', self.engine.base_dir / 'plugins'))

        if not plugins_dir.exists():
            return

        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                await self._load_plugin_from_directory(plugin_dir)

    async def _load_plugin_from_directory(self, plugin_dir: Path) -> None:
        """
        Load plugin from directory.

        Args:
            plugin_dir: Directory containing plugin files.
        """
        plugin_file = plugin_dir / 'plugin.py'
        if not plugin_file.exists():
            plugin_file = plugin_dir / '__init__.py'

        if not plugin_file.exists():
            return

        metadata_file = plugin_dir / 'plugin.json'
        metadata = {}
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                pass

        try:
            spec = importlib.util.spec_from_file_location(
                f"metupy_plugin_{plugin_dir.name}",
                plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, MetupyPlugin) and obj != MetupyPlugin:
                    plugin = obj(self.engine)
                    plugin.name = metadata.get('name', plugin.name)
                    plugin.version = metadata.get('version', plugin.version)
                    plugin.description = metadata.get('description', plugin.description)
                    self.plugins[plugin.name] = plugin
                    break

        except Exception as e:
            print(f"  Error loading plugin {plugin_dir.name}: {e}")

    async def _initialize_plugins(self) -> None:
        """Initialize active plugins."""
        active_names = getattr(self.engine.config, 'ACTIVE_PLUGINS', [])

        for plugin_name in active_names:
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name]

                if not self._check_dependencies(plugin):
                    print(f"  Plugin '{plugin_name}' has unmet dependencies")
                    continue

                try:
                    await plugin.setup()
                    self.active_plugins.append(plugin)
                    print(f"  Plugin loaded: {plugin.name} v{plugin.version}")
                except Exception as e:
                    print(f"  Failed to load plugin '{plugin_name}': {e}")

    def _check_dependencies(self, plugin: MetupyPlugin) -> bool:
        """
        Check plugin dependencies.

        Args:
            plugin: Plugin to check.

        Returns:
            True if all dependencies are met.
        """
        for dep in plugin.dependencies:
            if dep not in self.plugins:
                return False
            if dep not in [p.name for p in self.active_plugins]:
                return False
        return True

    def _register_hooks(self) -> None:
        """Register plugin hooks."""
        hook_methods = [
            'on_init',
            'on_build_start',
            'on_build_end',
            'on_page_before_render',
            'on_page_after_render',
        ]

        for hook_name in hook_methods:
            self.plugin_hooks[hook_name] = []
            for plugin in self.active_plugins:
                if hasattr(plugin, hook_name):
                    method = getattr(plugin, hook_name)
                    if callable(method):
                        self.plugin_hooks[hook_name].append(method)

    async def execute_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Execute plugin hook.

        Args:
            hook_name: Name of hook to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Hook result if any hook returns a value.
        """
        result = None

        if hook_name in self.plugin_hooks:
            for hook in self.plugin_hooks[hook_name]:
                hook_result = hook(*args, **kwargs)

                if hook_result is not None:
                    if hook_name == 'on_page_before_render':
                        kwargs['context'] = hook_result
                    elif hook_name == 'on_page_after_render':
                        result = hook_result
                        return result

        return kwargs.get('context') or kwargs.get('html') or result

    def register_template_extensions(self, env) -> None:
        """
        Register plugin template extensions.

        Args:
            env: Jinja2 Environment instance.
        """
        for plugin in self.active_plugins:
            plugin.register_filters(env)
            plugin.register_globals(env)

    def setup_routes(self, app) -> None:
        """
        Setup plugin API routes.

        Args:
            app: Aiohttp Application instance.
        """
        for plugin in self.active_plugins:
            plugin.setup_routes(app)

    def get_plugin(self, name: str) -> Optional[MetupyPlugin]:
        """
        Get plugin by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin instance or None.
        """
        return self.plugins.get(name)

    def list_active_plugins(self) -> List[str]:
        """
        List active plugin names.

        Returns:
            List of active plugin names.
        """
        return [plugin.name for plugin in self.active_plugins]