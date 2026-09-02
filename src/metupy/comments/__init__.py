# metupy/comments/__init__.py
"""Comments system untuk Metupy."""

__all__ = [
    "RedisCommentManager",
    "JSONCommentStorage",
]

def __getattr__(name):
    if name == "RedisCommentManager":
        from metupy.core.redis_manager import CommentRedisManager
        return CommentRedisManager
    elif name == "JSONCommentStorage":
        from metupy.core.json_storage import CommentJSONStorage
        return CommentJSONStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")