"""
Metupy Studio - Content Management System.

Provides web-based CMS for managing Metupy content.
"""

__all__ = [
    "StudioApp",
]


def __getattr__(name: str):
    """
    Lazy import for Studio classes.

    Args:
        name: Attribute name.

    Returns:
        Class or raises AttributeError.
    """
    if name == "StudioApp":
        from metupy.studio.app import StudioApp
        return StudioApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")