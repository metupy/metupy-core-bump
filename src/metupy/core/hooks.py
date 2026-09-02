# metupy/core/hooks.py
"""Hook System untuk Metupy."""

from typing import Dict, List, Any, Callable, Optional
import asyncio
import inspect

class HookManager:
    """Manages hooks and events."""
    
    def __init__(self, engine):
        self.engine = engine
        self.hooks: Dict[str, List[Callable]] = {}
        self.async_hooks: Dict[str, List[Callable]] = {}
        
    def register_hook(self, hook_name: str, callback: Callable, async_hook: bool = False):
        """Register a hook."""
        if async_hook:
            if hook_name not in self.async_hooks:
                self.async_hooks[hook_name] = []
            self.async_hooks[hook_name].append(callback)
        else:
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append(callback)
            
    def unregister_hook(self, hook_name: str, callback: Callable):
        """Unregister a hook."""
        if hook_name in self.hooks:
            self.hooks[hook_name].remove(callback)
        if hook_name in self.async_hooks:
            self.async_hooks[hook_name].remove(callback)
            
    async def execute_hook(self, hook_name: str, *args, **kwargs):
        """Execute a hook."""
        results = []
        
        # Execute sync hooks
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                result = callback(*args, **kwargs)
                if result is not None:
                    results.append(result)
                    
        # Execute async hooks
        if hook_name in self.async_hooks:
            for callback in self.async_hooks[hook_name]:
                if inspect.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                if result is not None:
                    results.append(result)
                    
        return results[-1] if results else None
        
    def register_default_hooks(self):
        """Register default Metupy hooks."""
        # Register built-in hooks
        self.register_hook('on_init', self._hook_init)
        self.register_hook('on_build_start', self._hook_build_start)
        self.register_hook('on_build_end', self._hook_build_end)
        self.register_hook('on_page_render', self._hook_page_render)
        
    def _hook_init(self, engine):
        """Default init hook."""
        print("🏗️  Initializing Metupy...")
        
    def _hook_build_start(self, engine):
        """Default build start hook."""
        print("🔨 Starting build process...")
        
    def _hook_build_end(self, engine):
        """Default build end hook."""
        print("✅ Build completed!")
        
    def _hook_page_render(self, page, context):
        """Default page render hook."""
        return context