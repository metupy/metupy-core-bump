"""
Hook system for Metupy.

Provides event hooks for extending functionality without
modifying core engine code.
"""

import inspect
from typing import Any, Callable, Dict, List, Optional


class HookManager:
    """Manage hooks and events for Metupy."""

    def __init__(self, engine=None):
        """
        Initialize HookManager.

        Args:
            engine: Optional MetupyEngine instance.
        """
        self.engine = engine
        self.hooks: Dict[str, List[Callable]] = {}
        self.async_hooks: Dict[str, List[Callable]] = {}

    def register_hook(self, hook_name: str, callback: Callable, is_async: bool = False) -> None:
        """
        Register a hook callback.

        Args:
            hook_name: Name of the hook.
            callback: Callable function.
            is_async: Whether callback is async.
        """
        if is_async:
            if hook_name not in self.async_hooks:
                self.async_hooks[hook_name] = []
            self.async_hooks[hook_name].append(callback)
        else:
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append(callback)

    def unregister_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Unregister a hook callback.

        Args:
            hook_name: Hook name.
            callback: Callback to remove.
        """
        if hook_name in self.hooks and callback in self.hooks[hook_name]:
            self.hooks[hook_name].remove(callback)

        if hook_name in self.async_hooks and callback in self.async_hooks[hook_name]:
            self.async_hooks[hook_name].remove(callback)

    async def execute_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Execute all callbacks for a hook.

        Args:
            hook_name: Hook name to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Last non-None result from callbacks.
        """
        results = []

        for callback in self.hooks.get(hook_name, []):
            result = callback(*args, **kwargs)
            if result is not None:
                results.append(result)

        for callback in self.async_hooks.get(hook_name, []):
            if inspect.iscoroutinefunction(callback):
                result = await callback(*args, **kwargs)
            else:
                result = callback(*args, **kwargs)

            if result is not None:
                results.append(result)

        return results[-1] if results else None

    def register_default_hooks(self) -> None:
        """Register default Metupy hooks."""
        self.register_hook('on_init', self._hook_init)
        self.register_hook('on_build_start', self._hook_build_start)
        self.register_hook('on_build_end', self._hook_build_end)

    def _hook_init(self, engine) -> None:
        """Default init hook."""
        print("  Initializing Metupy...")

    def _hook_build_start(self, engine) -> None:
        """Default build start hook."""
        print("  Starting build...")

    def _hook_build_end(self, engine) -> None:
        """Default build end hook."""
        print("  Build completed.")

    def clear_hooks(self, hook_name: Optional[str] = None) -> None:
        """
        Clear hooks.

        Args:
            hook_name: Specific hook to clear, or all if None.
        """
        if hook_name:
            self.hooks.pop(hook_name, None)
            self.async_hooks.pop(hook_name, None)
        else:
            self.hooks.clear()
            self.async_hooks.clear()