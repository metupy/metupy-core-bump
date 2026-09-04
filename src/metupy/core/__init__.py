"""
Core components for Metupy.

All imports are lazy to avoid circular dependencies.
"""

__all__ = [
    "MetupyEngine",
    "MetupyPlugin",
    "PluginManager",
    "Theme",
    "ThemeManager",
    "MetupyWidget",
    "WidgetManager",
    "ContentManager",
    "PageManager",
    "HookManager",
    "SecurityManager",
    "MacroManager",
    "RuntimeManager",
    "PYMExecutor",
]


def __getattr__(name: str):
    """
    Lazy import for core classes.

    Args:
        name: Attribute name.

    Returns:
        Class or raises AttributeError.
    """
    if name == "MetupyEngine":
        from metupy.core.engine import MetupyEngine
        return MetupyEngine
    elif name == "MetupyPlugin" or name == "PluginManager":
        from metupy.core.plugin_manager import MetupyPlugin, PluginManager
        return MetupyPlugin if name == "MetupyPlugin" else PluginManager
    elif name == "Theme" or name == "ThemeManager":
        from metupy.core.theme_manager import Theme, ThemeManager
        return Theme if name == "Theme" else ThemeManager
    elif name == "MetupyWidget" or name == "WidgetManager":
        from metupy.core.widget_manager import MetupyWidget, WidgetManager
        return MetupyWidget if name == "MetupyWidget" else WidgetManager
    elif name == "ContentManager":
        from metupy.core.content_manager import ContentManager
        return ContentManager
    elif name == "PageManager":
        from metupy.core.page_manager import PageManager
        return PageManager
    elif name == "HookManager":
        from metupy.core.hooks import HookManager
        return HookManager
    elif name == "SecurityManager":
        from metupy.core.security import SecurityManager
        return SecurityManager
    elif name == "MacroManager":
        from metupy.core.macros import MacroManager
        return MacroManager
    elif name == "RuntimeManager":
        from metupy.core.runtime_manager import RuntimeManager
        return RuntimeManager
    elif name == "PYMExecutor":
        from metupy.core.pym_executor import PYMExecutor
        return PYMExecutor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")