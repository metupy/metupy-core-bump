# metupy/models/__init__.py
"""Database models for Metupy."""

# Lazy imports to avoid circular dependencies
__all__ = [
    "BaseModel",
    "DatabaseManager",
    "init_database",
    "User",
    "PageModel",
    "PluginModel",
    "ThemeModel",
    "WidgetModel",
    "CommentModel",
    "SessionModel",
    "ActivityLogModel",
]

def __getattr__(name):
    if name == "BaseModel" or name == "DatabaseManager" or name == "init_database":
        from metupy.models.base import BaseModel, DatabaseManager, init_database
        return locals()[name]
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
    elif name == "SessionModel":
        from metupy.models.session import SessionModel
        return SessionModel
    elif name == "ActivityLogModel":
        from metupy.models.activity import ActivityLogModel
        return ActivityLogModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")