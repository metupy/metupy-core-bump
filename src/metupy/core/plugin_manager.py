# metupy/core/plugin_manager.py
"""Plugin Manager - Mengelola plugin Metupy."""

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Type, Optional
from abc import ABC, abstractmethod

from metupy.core.hooks import HookManager

class MetupyPlugin(ABC):
    """Base class for Metupy plugins."""
    
    # Plugin metadata
    name: str = "base-plugin"
    version: str = "0.1.0"
    description: str = "Base plugin"
    author: str = "Unknown"
    url: str = ""
    license: str = "MIT"
    
    # Plugin dependencies
    dependencies: List[str] = []
    
    # Plugin settings
    settings: Dict[str, Any] = {}
    
    def __init__(self, engine):
        self.engine = engine
        self.config = engine.config
        self.logger = engine.logger if hasattr(engine, 'logger') else None
        
    @abstractmethod
    def setup(self):
        """Setup plugin."""
        pass
        
    def on_init(self, engine):
        """Called when engine initializes."""
        pass
        
    def on_build_start(self, engine):
        """Called when build starts."""
        pass
        
    def on_build_end(self, engine):
        """Called when build ends."""
        pass
        
    def on_page_before_render(self, page, context):
        """Called before page render."""
        return context
        
    def on_page_after_render(self, page, html):
        """Called after page render."""
        return html
        
    def register_filters(self, env):
        """Register custom Jinja2 filters."""
        pass
        
    def register_globals(self, env):
        """Register custom Jinja2 globals."""
        pass
        
    def setup_routes(self, app):
        """Setup API routes."""
        pass
        
    def cleanup(self):
        """Cleanup plugin."""
        pass

class PluginManager:
    """Manages Metupy plugins."""
    
    def __init__(self, engine):
        self.engine = engine
        self.plugins: Dict[str, MetupyPlugin] = {}
        self.active_plugins: List[MetupyPlugin] = []
        self.plugin_hooks = {}
        
    async def load_plugins(self):
        """Load all plugins."""
        # Load built-in plugins
        self._load_builtin_plugins()
        
        # Load user plugins
        await self._load_user_plugins()
        
        # Initialize active plugins
        await self._initialize_plugins()
        
        # Register hooks
        self._register_hooks()
        
    def _load_builtin_plugins(self):
        """Load built-in plugins."""
        from metupy.plugins import (
            SEOPlugin,
            SitemapPlugin,
            RSSPlugin,
            SearchPlugin,
            CommentsPlugin,
            AnalyticsPlugin,
        )
        
        builtin_plugins = [
            SEOPlugin,
            SitemapPlugin,
            RSSPlugin,
            SearchPlugin,
            CommentsPlugin,
            AnalyticsPlugin,
        ]
        
        for plugin_class in builtin_plugins:
            plugin = plugin_class(self.engine)
            self.plugins[plugin.name] = plugin
            
    async def _load_user_plugins(self):
        """Load user plugins from plugins directory."""
        plugins_dir = Path(self.engine.config.PLUGINS_DIR)
        
        if not plugins_dir.exists():
            return
            
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                await self._load_plugin_from_directory(plugin_dir)
                
    async def _load_plugin_from_directory(self, plugin_dir: Path):
        """Load plugin from directory."""
        try:
            # Check for plugin.py
            plugin_file = plugin_dir / 'plugin.py'
            if not plugin_file.exists():
                plugin_file = plugin_dir / '__init__.py'
                
            if not plugin_file.exists():
                return
                
            # Load plugin metadata
            metadata_file = plugin_dir / 'plugin.json'
            metadata = {}
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                
            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"metupy_plugin_{plugin_dir.name}",
                plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, MetupyPlugin):
                    if obj != MetupyPlugin:
                        plugin = obj(self.engine)
                        plugin.name = metadata.get('name', plugin.name)
                        plugin.version = metadata.get('version', plugin.version)
                        plugin.description = metadata.get('description', plugin.description)
                        self.plugins[plugin.name] = plugin
                        break
                        
        except Exception as e:
            print(f"Error loading plugin {plugin_dir.name}: {e}")
            
    async def _initialize_plugins(self):
        """Initialize active plugins."""
        active_names = self.engine.config.ACTIVE_PLUGINS
        
        for plugin_name in active_names:
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name]
                
                # Check dependencies
                if not self._check_dependencies(plugin):
                    print(f"Plugin {plugin_name} has unmet dependencies")
                    continue
                    
                try:
                    await plugin.setup()
                    self.active_plugins.append(plugin)
                    print(f"  ✓ Plugin loaded: {plugin.name} v{plugin.version}")
                except Exception as e:
                    print(f"  ✗ Failed to load plugin {plugin_name}: {e}")
                    
    def _check_dependencies(self, plugin: MetupyPlugin) -> bool:
        """Check plugin dependencies."""
        for dep in plugin.dependencies:
            if dep not in self.plugins:
                return False
            if dep not in [p.name for p in self.active_plugins]:
                return False
        return True
        
    def _register_hooks(self):
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
                        
    async def execute_hook(self, hook_name: str, *args, **kwargs):
        """Execute plugin hook."""
        if hook_name in self.plugin_hooks:
            for hook in self.plugin_hooks[hook_name]:
                result = await hook(*args, **kwargs)
                if result is not None and hook_name == 'on_page_before_render':
                    kwargs['context'] = result
                elif result is not None and hook_name == 'on_page_after_render':
                    return result
        return kwargs.get('context') or kwargs.get('html') or None
        
    def register_template_extensions(self, env):
        """Register template extensions from plugins."""
        for plugin in self.active_plugins:
            plugin.register_filters(env)
            plugin.register_globals(env)
            
    def setup_routes(self, app):
        """Setup routes from plugins."""
        for plugin in self.active_plugins:
            plugin.setup_routes(app)
            
    def get_plugin(self, name: str) -> Optional[MetupyPlugin]:
        """Get plugin by name."""
        return self.plugins.get(name)
        
    def list_active_plugins(self) -> List[str]:
        """List active plugins."""
        return [plugin.name for plugin in self.active_plugins]