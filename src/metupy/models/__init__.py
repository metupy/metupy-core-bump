"""
Database models for Metupy.

All models use UUID4 primary keys.
Lazy imports to avoid circular dependencies.
"""

__all__ = [
    "BaseModel",
    "DatabaseManager",
    "User",
    "PageModel",
    "PluginModel",
    "ThemeModel",
    "WidgetModel",
    "CommentModel",
]


def __getattr__(name: str):
    """
    Lazy import for model classes.

    Args:
        name: Attribute name.

    Returns:
        Model class or raises AttributeError.
    """
    if name == "BaseModel" or name == "DatabaseManager":
        from metupy.models.base import BaseModel, DatabaseManager
        return BaseModel if name == "BaseModel" else DatabaseManager
    elif name == "User":
        from metupy.models.user import User
        return User
    elif name == "PageModel":
        from metupy.models.page import PageModel
        return PageModel
    elif name == "PluginModel":
        from metupy.models.plugin import PluginModel
        return PluginModel
    elif name == "ThemeModel":
        from metupy.models.theme import ThemeModel
        return ThemeModel
    elif name == "WidgetModel":
        from metupy.models.widget import WidgetModel
        return WidgetModel
    elif name == "CommentModel":
        from metupy.models.comment import CommentModel
        return CommentModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")