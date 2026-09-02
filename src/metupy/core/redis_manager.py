# metupy/core/redis_manager.py
"""Redis Manager untuk Metupy."""

import redis
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

class RedisManager:
    """Generic Redis manager."""
    
    def __init__(self, engine):
        self.engine = engine
        self.redis_client = self._create_client()
        self.prefix = getattr(engine.config, 'CACHE_PREFIX', 'metupy')
        
    def _create_client(self) -> redis.Redis:
        """Create Redis client."""
        return redis.Redis(
            host=getattr(self.engine.config, 'CACHE_HOST', 'localhost'),
            port=getattr(self.engine.config, 'CACHE_PORT', 6379),
            db=getattr(self.engine.config, 'CACHE_DB', 0),
            password=getattr(self.engine.config, 'CACHE_PASSWORD', None),
            decode_responses=True,
        )
        
    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """Set value in Redis."""
        try:
            full_key = f"{self.prefix}:{key}"
            serialized = json.dumps(value, default=str)
            
            if expiry:
                self.redis_client.setex(full_key, expiry, serialized)
            else:
                self.redis_client.set(full_key, serialized)
                
            return True
        except Exception as e:
            print(f"Error setting Redis key: {e}")
            return False
            
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            full_key = f"{self.prefix}:{key}"
            value = self.redis_client.get(full_key)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error getting Redis key: {e}")
            return None
            
    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            full_key = f"{self.prefix}:{key}"
            self.redis_client.delete(full_key)
            return True
        except Exception as e:
            print(f"Error deleting Redis key: {e}")
            return False
            
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            full_key = f"{self.prefix}:{key}"
            return self.redis_client.exists(full_key) > 0
        except Exception:
            return False
            
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on key."""
        try:
            full_key = f"{self.prefix}:{key}"
            self.redis_client.expire(full_key, seconds)
            return True
        except Exception:
            return False
            
    def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field."""
        try:
            full_key = f"{self.prefix}:{key}"
            self.redis_client.hset(full_key, field, json.dumps(value, default=str))
            return True
        except Exception as e:
            print(f"Error setting Redis hash: {e}")
            return False
            
    def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field."""
        try:
            full_key = f"{self.prefix}:{key}"
            value = self.redis_client.hget(full_key, field)
            
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
            
    def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        try:
            full_key = f"{self.prefix}:{key}"
            data = self.redis_client.hgetall(full_key)
            return {k: json.loads(v) for k, v in data.items()}
        except Exception:
            return {}
            
    def hdel(self, key: str, field: str) -> bool:
        """Delete hash field."""
        try:
            full_key = f"{self.prefix}:{key}"
            self.redis_client.hdel(full_key, field)
            return True
        except Exception:
            return False
            
    def clear_all(self):
        """Clear all Metupy keys."""
        try:
            pattern = f"{self.prefix}:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        except Exception as e:
            print(f"Error clearing Redis: {e}")
            
    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.redis_client.ping()
        except Exception:
            return False


class CommentRedisManager:
    """Redis Manager khusus untuk comments."""
    
    def __init__(self, engine):
        self.engine = engine
        self.redis_client = self._create_client()
        self.prefix = f"{getattr(engine.config, 'CACHE_PREFIX', 'metupy')}:comments"
        
    def _create_client(self) -> redis.Redis:
        """Create Redis client."""
        return redis.Redis(
            host=getattr(self.engine.config, 'CACHE_HOST', 'localhost'),
            port=getattr(self.engine.config, 'CACHE_PORT', 6379),
            db=getattr(self.engine.config, 'CACHE_DB', 0),
            password=getattr(self.engine.config, 'CACHE_PASSWORD', None),
            decode_responses=True,
        )
        
    def add_comment(self, comment_data: Dict) -> bool:
        """Add comment to Redis."""
        try:
            post_slug = comment_data.get('post_slug')
            comment_id = comment_data.get('id', str(uuid.uuid4()))
            
            key = f"{self.prefix}:{post_slug}"
            sorted_key = f"{key}:sorted"
            
            # Store comment
            self.redis_client.hset(key, comment_id, json.dumps(comment_data, default=str))
            
            # Add to sorted set
            score = datetime.now().timestamp()
            self.redis_client.zadd(sorted_key, {comment_id: score})
            
            # Set expiry (24 hours)
            self.redis_client.expire(key, 86400)
            self.redis_client.expire(sorted_key, 86400)
            
            return True
        except Exception as e:
            print(f"Error adding comment to Redis: {e}")
            return False
            
    def get_comments(self, post_slug: str, limit: int = 100) -> List[Dict]:
        """Get comments from Redis."""
        try:
            key = f"{self.prefix}:{post_slug}"
            sorted_key = f"{key}:sorted"
            
            # Get comment IDs
            comment_ids = self.redis_client.zrevrange(sorted_key, 0, limit - 1)
            
            comments = []
            for comment_id in comment_ids:
                comment_data = self.redis_client.hget(key, comment_id)
                if comment_data:
                    comments.append(json.loads(comment_data))
                    
            return comments
        except Exception as e:
            print(f"Error getting comments from Redis: {e}")
            return []
            
    def get_all_comments(self) -> Dict[str, List[Dict]]:
        """Get all comments from Redis."""
        try:
            result = {}
            pattern = f"{self.prefix}:*"
            
            for key in self.redis_client.scan_iter(match=pattern):
                if ':sorted' in key:
                    continue
                    
                post_slug = key.split(':')[-1]
                comments = self.get_comments(post_slug)
                if comments:
                    result[post_slug] = comments
                    
            return result
        except Exception as e:
            print(f"Error getting all comments: {e}")
            return {}
            
    def clear_all(self):
        """Clear all comments from Redis."""
        try:
            pattern = f"{self.prefix}:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        except Exception as e:
            print(f"Error clearing Redis: {e}")