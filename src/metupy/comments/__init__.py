"""
Comments system for Metupy.

Lazy imports for comment-related classes.
"""

__all__ = [
    "RedisCommentManager",
    "JSONCommentStorage",
]


def __getattr__(name: str):
    """
    Lazy import for comment classes.

    Args:
        name: Attribute name.

    Returns:
        Class or raises AttributeError.
    """
    if name == "RedisCommentManager":
        from metupy.core.redis_manager import CommentRedisManager
        return CommentRedisManager
    elif name == "JSONCommentStorage":
        from metupy.core.json_storage import CommentJSONStorage
        return CommentJSONStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")