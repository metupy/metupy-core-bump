"""
Redis manager for Metupy.

Provides Redis caching for comments and other data.
Redis is optional - falls back to memory when unavailable.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class RedisManager:
    """Generic Redis manager."""

    def __init__(self, engine):
        """
        Initialize RedisManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.prefix = getattr(engine.config, 'CACHE_PREFIX', 'metupy')
        self.redis_client = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis if available."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=getattr(self.engine.config, 'CACHE_HOST', 'localhost'),
                port=getattr(self.engine.config, 'CACHE_PORT', 6379),
                db=getattr(self.engine.config, 'CACHE_DB', 0),
                password=getattr(self.engine.config, 'CACHE_PASSWORD', None),
                decode_responses=True,
            )
            self.redis_client.ping()
        except ImportError:
            self.redis_client = None
        except Exception:
            self.redis_client = None

    def is_available(self) -> bool:
        """
        Check if Redis is available.

        Returns:
            True if connected.
        """
        return self.redis_client is not None

    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Set value in Redis.

        Args:
            key: Cache key.
            value: Value to store.
            expiry: Optional TTL in seconds.

        Returns:
            True if successful.
        """
        if not self.redis_client:
            return False

        try:
            full_key = f"{self.prefix}:{key}"
            serialized = json.dumps(value, default=str)

            if expiry:
                self.redis_client.setex(full_key, expiry, serialized)
            else:
                self.redis_client.set(full_key, serialized)
            return True
        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis.

        Args:
            key: Cache key.

        Returns:
            Stored value or None.
        """
        if not self.redis_client:
            return None

        try:
            full_key = f"{self.prefix}:{key}"
            value = self.redis_client.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    def delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Cache key.

        Returns:
            True if successful.
        """
        if not self.redis_client:
            return False

        try:
            full_key = f"{self.prefix}:{key}"
            self.redis_client.delete(full_key)
            return True
        except Exception:
            return False

    def clear_all(self) -> None:
        """Clear all Metupy keys from Redis."""
        if not self.redis_client:
            return

        try:
            pattern = f"{self.prefix}:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        except Exception:
            pass


class CommentRedisManager:
    """Redis manager specifically for comments."""

    def __init__(self, engine):
        """
        Initialize CommentRedisManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.prefix = f"{getattr(engine.config, 'CACHE_PREFIX', 'metupy')}:comments"
        self.redis_client = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis if available."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=getattr(self.engine.config, 'CACHE_HOST', 'localhost'),
                port=getattr(self.engine.config, 'CACHE_PORT', 6379),
                db=getattr(self.engine.config, 'CACHE_DB', 0),
                password=getattr(self.engine.config, 'CACHE_PASSWORD', None),
                decode_responses=True,
            )
            self.redis_client.ping()
        except ImportError:
            self.redis_client = None
        except Exception:
            self.redis_client = None

    def add_comment(self, comment: Dict[str, Any]) -> bool:
        """
        Add comment to Redis.

        Args:
            comment: Comment dictionary.

        Returns:
            True if successful.
        """
        if not self.redis_client:
            return False

        try:
            post_slug = comment.get('post_slug')
            comment_id = comment.get('id')

            key = f"{self.prefix}:{post_slug}"
            sorted_key = f"{key}:sorted"

            self.redis_client.hset(key, comment_id, json.dumps(comment, default=str))

            score = datetime.now().timestamp()
            self.redis_client.zadd(sorted_key, {comment_id: score})

            self.redis_client.expire(key, 86400)
            self.redis_client.expire(sorted_key, 86400)

            return True
        except Exception:
            return False

    def get_comments(self, post_slug: str, limit: int = 100) -> List[Dict]:
        """
        Get comments from Redis.

        Args:
            post_slug: Post slug.
            limit: Maximum comments to return.

        Returns:
            List of comment dictionaries.
        """
        if not self.redis_client:
            return []

        try:
            key = f"{self.prefix}:{post_slug}"
            sorted_key = f"{key}:sorted"

            comment_ids = self.redis_client.zrevrange(sorted_key, 0, limit - 1)

            comments = []
            for comment_id in comment_ids:
                comment_data = self.redis_client.hget(key, comment_id)
                if comment_data:
                    comments.append(json.loads(comment_data))

            return comments
        except Exception:
            return []

    def clear_all(self) -> None:
        """Clear all comments from Redis."""
        if not self.redis_client:
            return

        try:
            pattern = f"{self.prefix}:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        except Exception:
            pass