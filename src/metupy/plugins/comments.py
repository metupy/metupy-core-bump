"""
Comments plugin for Metupy.

Provides comment functionality with memory storage as fallback.
Supports Redis and JSON storage when available.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from metupy.core.plugin_manager import MetupyPlugin


class CommentsPlugin(MetupyPlugin):
    """Comment system plugin."""

    name = "comments"
    version = "1.0.0"
    description = "Comment system with pluggable storage"
    author = "Metupy Team"

    def __init__(self, engine):
        """Initialize comments plugin."""
        super().__init__(engine)
        self.redis_manager = None
        self.json_storage = None
        self.comments_config = {}
        self.comments: List[Dict[str, Any]] = []
        self.security = None

    def setup(self) -> None:
        """Setup comments plugin."""
        self.comments_config = getattr(self.engine.config, 'COMMENTS', {})

        self.security = getattr(self.engine, 'security', None)
        if not self.security:
            from metupy.core.security import SecurityManager
            self.security = SecurityManager(self.engine)

        storage = self.comments_config.get('storage', 'memory')

        if storage == 'redis':
            try:
                from metupy.core.redis_manager import CommentRedisManager
                self.redis_manager = CommentRedisManager(self.engine)
                print(f"  Comments Plugin: Redis storage")
            except ImportError:
                print(f"  Comments Plugin: Redis not available, using memory")
                self.redis_manager = None

        print(f"  Comments Plugin v{self.version} loaded")

    def setup_routes(self, app) -> None:
        """Setup comment API routes."""
        from aiohttp import web

        app.router.add_post('/api/comments', self.create_comment)
        app.router.add_get('/api/comments/{post_slug}', self.get_comments)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/like', self.like_comment)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/approve', self.approve_comment)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/spam', self.mark_as_spam)
        app.router.add_delete('/api/comments/{post_slug}/{comment_id}', self.delete_comment)

    async def create_comment(self, request):
        """
        Create a new comment.

        Args:
            request: Aiohttp request object.

        Returns:
            JSON response.
        """
        from aiohttp import web

        try:
            data = await request.json()
        except Exception:
            return web.json_response({'success': False, 'error': 'Invalid JSON'}, status=400)

        required = ['post_slug', 'author_name', 'author_email', 'content']
        for field in required:
            if field not in data or not data[field]:
                return web.json_response(
                    {'success': False, 'error': f'Missing field: {field}'},
                    status=400
                )

        if self.security and hasattr(self.security, 'validate_email'):
            if not self.security.validate_email(data['author_email']):
                return web.json_response(
                    {'success': False, 'error': 'Invalid email address'},
                    status=400
                )

        content = data['content']
        if self.security and hasattr(self.security, 'sanitize_input'):
            content = self.security.sanitize_input(content)

        if self._is_spam(data):
            return web.json_response(
                {'success': False, 'error': 'Comment flagged as spam'},
                status=403
            )

        comment = {
            'id': str(uuid.uuid4()),
            'post_slug': data['post_slug'],
            'author_name': data['author_name'],
            'author_email': data['author_email'],
            'author_website': data.get('author_website'),
            'content': content,
            'parent_id': None,
            'is_approved': not self.comments_config.get('moderation', False),
            'is_spam': False,
            'likes': 0,
            'dislikes': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': None,
        }

        self.comments.append(comment)

        if self.redis_manager:
            try:
                self.redis_manager.add_comment(comment)
            except Exception:
                pass

        return web.json_response({'success': True, 'comment': comment}, status=201)

    async def get_comments(self, request):
        """
        Get comments for a post.

        Args:
            request: Aiohttp request object.

        Returns:
            JSON response with comments.
        """
        from aiohttp import web

        post_slug = request.match_info['post_slug']

        if self.redis_manager:
            try:
                comments = self.redis_manager.get_comments(post_slug)
                if comments:
                    return web.json_response({
                        'success': True,
                        'comments': comments,
                        'source': 'redis',
                    })
            except Exception:
                pass

        comments = [
            c for c in self.comments
            if c['post_slug'] == post_slug and c['is_approved'] and not c['is_spam']
        ]

        return web.json_response({
            'success': True,
            'comments': comments,
            'source': 'memory',
        })

    async def like_comment(self, request):
        """
        Like a comment.

        Args:
            request: Aiohttp request object.

        Returns:
            JSON response.
        """
        from aiohttp import web

        comment_id = request.match_info['comment_id']

        comment = next((c for c in self.comments if c['id'] == comment_id), None)
        if not comment:
            return web.json_response({'success': False, 'error': 'Comment not found'}, status=404)

        comment['likes'] = comment.get('likes', 0) + 1

        return web.json_response({'success': True, 'likes': comment['likes']})

    async def approve_comment(self, request):
        """
        Approve a comment.

        Args:
            request: Aiohttp request object.

        Returns:
            JSON response.
        """
        from aiohttp import web

        comment_id = request.match_info['comment_id']

        comment = next((c for c in self.comments if c['id'] == comment_id), None)
        if not comment:
            return web.json_response({'success': False, 'error': 'Comment not found'}, status=404)

        comment['is_approved'] = True
        comment['is_spam'] = False

        return web.json_response({'success': True, 'comment': comment})

    async def mark_as_spam(self, request):
        """
        Mark comment as spam.

        Args:
            request: Aiohttp request object.

        Returns:
            JSON response.
        """
        from aiohttp import web

        comment_id = request.match_info['comment_id']

        comment = next((c for c in self.comments if c['id'] == comment_id), None)
        if not comment:
            return web.json_response({'success': False, 'error': 'Comment not found'}, status=404)

        comment['is_spam'] = True
        comment['is_approved'] = False

        return web.json_response({'success': True, 'comment': comment})

    async def delete_comment(self, request):
        """
        Delete a comment.

        Args:
            request: Aiohttp request object.

        Returns:
            JSON response.
        """
        from aiohttp import web

        comment_id = request.match_info['comment_id']

        self.comments = [c for c in self.comments if c['id'] != comment_id]

        return web.json_response({'success': True})

    def _is_spam(self, data: Dict[str, Any]) -> bool:
        """
        Check if comment is spam.

        Args:
            data: Comment data.

        Returns:
            True if comment is spam.
        """
        content = data.get('content', '').lower()

        spam_keywords = ['viagra', 'casino', 'lottery', 'bitcoin', 'crypto', 'porn']
        for keyword in spam_keywords:
            if keyword in content:
                return True

        links = re.findall(r'https?://', content)
        if len(links) > 3:
            return True

        if re.search(r'(.)\1{4,}', content):
            return True

        return False

    def register_filters(self, env) -> None:
        """Register comment Jinja2 filters."""
        env.filters['comment_count'] = self.get_comment_count

    def get_comment_count(self, post_slug: str) -> int:
        """
        Get comment count for a post.

        Args:
            post_slug: Post slug.

        Returns:
            Number of approved comments.
        """
        return len([
            c for c in self.comments
            if c['post_slug'] == post_slug and c['is_approved'] and not c['is_spam']
        ])

    def get_comments_for_template(self, post_slug: str) -> List[Dict[str, Any]]:
        """
        Get comments for template rendering.

        Args:
            post_slug: Post slug.

        Returns:
            List of comment dictionaries.
        """
        return [
            c for c in self.comments
            if c['post_slug'] == post_slug and c['is_approved'] and not c['is_spam']
        ]