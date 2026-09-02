# metupy/plugins/comments.py
"""Comments Plugin - Sistem komentar lengkap."""

from metupy.core.plugin_manager import MetupyPlugin
from metupy.models.comment import CommentModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
import uuid

class CommentsPlugin(MetupyPlugin):
    """Comments plugin with Redis caching."""
    
    name = "comments"
    version = "1.0.0"
    description = "Comment system with Redis caching"
    author = "Metupy Team"
    url = "https://metupy.dev/plugins/comments"
    
    def __init__(self, engine):
        super().__init__(engine)
        self.redis_manager = None
        self.json_storage = None
        self.comments_config = {}
        
    def setup(self):
        """Setup comments plugin."""
        self.comments_config = self.engine.config.COMMENTS
        
        # Initialize storage
        if self.comments_config.get('storage') == 'redis':
            from metupy.core.redis_manager import RedisCommentManager
            self.redis_manager = RedisCommentManager(self.engine.config)
            
        from metupy.core.json_storage import JSONCommentStorage
        self.json_storage = JSONCommentStorage(self.engine.config)
        
        print(f"Comments Plugin v{self.version} initialized")
        
    def setup_routes(self, app):
        """Setup comment routes."""
        from aiohttp import web
        
        app.router.add_post('/api/comments', self.create_comment)
        app.router.add_get('/api/comments/{post_slug}', self.get_comments)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/reply', self.reply_to_comment)
        app.router.add_put('/api/comments/{post_slug}/{comment_id}', self.update_comment)
        app.router.add_delete('/api/comments/{post_slug}/{comment_id}', self.delete_comment)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/like', self.like_comment)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/dislike', self.dislike_comment)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/approve', self.approve_comment)
        app.router.add_post('/api/comments/{post_slug}/{comment_id}/spam', self.mark_as_spam)
        
    async def create_comment(self, request):
        """Create new comment."""
        from aiohttp import web
        
        data = await request.json()
        
        # Validate
        required = ['post_slug', 'author_name', 'author_email', 'content']
        for field in required:
            if field not in data:
                return web.json_response({
                    'success': False,
                    'error': f'Missing field: {field}'
                }, status=400)
                
        # Validate email
        if not self.engine.security.validate_email(data['author_email']):
            return web.json_response({
                'success': False,
                'error': 'Invalid email address'
            }, status=400)
            
        # Sanitize content
        content = self.engine.security.sanitize_input(data['content'])
        
        # Check rate limit
        if not await self._check_rate_limit(request):
            return web.json_response({
                'success': False,
                'error': 'Rate limit exceeded'
            }, status=429)
            
        # Check spam
        if await self._is_spam(data):
            return web.json_response({
                'success': False,
                'error': 'Comment flagged as spam'
            }, status=403)
            
        # Create comment
        comment = CommentModel.create(
            post_slug=data['post_slug'],
            author_name=data['author_name'],
            author_email=data['author_email'],
            author_website=data.get('author_website'),
            content=content,
            ip_address=request.remote,
            user_agent=request.headers.get('User-Agent', ''),
        )
        
        # Store in Redis for fast access
        if self.redis_manager:
            self.redis_manager.add_comment(comment)
            
        # Send notification
        if self.comments_config.get('notifications'):
            await self._send_notification(comment)
            
        return web.json_response({
            'success': True,
            'comment': comment.to_dict(),
        }, status=201)
        
    async def get_comments(self, request):
        """Get comments for a post."""
        from aiohttp import web
        
        post_slug = request.match_info['post_slug']
        
        # Try Redis first
        if self.redis_manager:
            comments = self.redis_manager.get_comments(post_slug)
            if comments:
                return web.json_response({
                    'success': True,
                    'comments': [c.to_dict() for c in comments],
                    'source': 'redis',
                })
                
        # Fallback to database
        comments = CommentModel.select().where(
            CommentModel.post_slug == post_slug,
            CommentModel.is_approved == True,
            CommentModel.is_spam == False,
        ).order_by(CommentModel.created_at)
        
        return web.json_response({
            'success': True,
            'comments': [c.to_dict() for c in comments],
            'source': 'database',
        })
        
    async def reply_to_comment(self, request):
        """Reply to comment."""
        from aiohttp import web
        
        post_slug = request.match_info['post_slug']
        comment_id = request.match_info['comment_id']
        data = await request.json()
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            parent_comment = CommentModel.get_by_id(comment_uuid)
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Parent comment not found'
            }, status=404)
            
        # Check max depth
        if self.comments_config.get('max_depth'):
            depth = self._get_comment_depth(parent_comment)
            if depth >= self.comments_config['max_depth']:
                return web.json_response({
                    'success': False,
                    'error': 'Maximum comment depth reached'
                }, status=400)
                
        # Create reply
        reply = CommentModel.create(
            post_slug=post_slug,
            parent=parent_comment,
            author_name=data['author_name'],
            author_email=data['author_email'],
            content=self.engine.security.sanitize_input(data['content']),
            ip_address=request.remote,
        )
        
        return web.json_response({
            'success': True,
            'comment': reply.to_dict(),
        }, status=201)
        
    async def update_comment(self, request):
        """Update comment."""
        from aiohttp import web
        
        post_slug = request.match_info['post_slug']
        comment_id = request.match_info['comment_id']
        data = await request.json()
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            comment = CommentModel.get_by_id(comment_uuid)
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
            
        # Update content
        if 'content' in data:
            comment.content = self.engine.security.sanitize_input(data['content'])
            comment.is_edited = True
            comment.edited_at = datetime.now()
            
        comment.save()
        
        return web.json_response({
            'success': True,
            'comment': comment.to_dict(),
        })
        
    async def delete_comment(self, request):
        """Delete comment."""
        from aiohttp import web
        
        post_slug = request.match_info['post_slug']
        comment_id = request.match_info['comment_id']
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            comment = CommentModel.get_by_id(comment_uuid)
            comment.delete_instance()
            
            return web.json_response({'success': True})
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
            
    async def like_comment(self, request):
        """Like comment."""
        from aiohttp import web
        
        comment_id = request.match_info['comment_id']
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            comment = CommentModel.get_by_id(comment_uuid)
            comment.like()
            
            return web.json_response({
                'success': True,
                'likes': comment.likes,
            })
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
            
    async def dislike_comment(self, request):
        """Dislike comment."""
        from aiohttp import web
        
        comment_id = request.match_info['comment_id']
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            comment = CommentModel.get_by_id(comment_uuid)
            comment.dislike()
            
            return web.json_response({
                'success': True,
                'dislikes': comment.dislikes,
            })
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
            
    async def approve_comment(self, request):
        """Approve comment."""
        from aiohttp import web
        
        comment_id = request.match_info['comment_id']
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            comment = CommentModel.get_by_id(comment_uuid)
            comment.approve()
            
            return web.json_response({
                'success': True,
                'comment': comment.to_dict(),
            })
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
            
    async def mark_as_spam(self, request):
        """Mark comment as spam."""
        from aiohttp import web
        
        comment_id = request.match_info['comment_id']
        
        try:
            comment_uuid = uuid.UUID(comment_id)
            comment = CommentModel.get_by_id(comment_uuid)
            comment.mark_as_spam()
            
            return web.json_response({
                'success': True,
                'comment': comment.to_dict(),
            })
        except (ValueError, CommentModel.DoesNotExist):
            return web.json_response({
                'success': False,
                'error': 'Comment not found'
            }, status=404)
            
    async def _check_rate_limit(self, request) -> bool:
        """Check rate limit."""
        rate_limit = self.comments_config.get('rate_limit', {})
        per_minute = rate_limit.get('per_minute', 5)
        per_hour = rate_limit.get('per_hour', 20)
        
        # Simple rate limiting using memory
        # In production, use Redis for rate limiting
        ip = request.remote
        
        return True
        
    async def _is_spam(self, data: Dict) -> bool:
        """Check if comment is spam."""
        content = data.get('content', '').lower()
        
        # Check spam keywords
        spam_keywords = ['viagra', 'casino', 'lottery', 'bitcoin', 'crypto', 'porn']
        for keyword in spam_keywords:
            if keyword in content:
                return True
                
        # Check for too many links
        links = re.findall(r'https?://', content)
        if len(links) > 3:
            return True
            
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', content):
            return True
            
        return False
        
    def _get_comment_depth(self, comment, depth: int = 0) -> int:
        """Get comment depth."""
        if comment.parent:
            return self._get_comment_depth(comment.parent, depth + 1)
        return depth
        
    async def _send_notification(self, comment):
        """Send notification email."""
        # Implementation for sending notification
        pass
        
    def register_filters(self, env):
        """Register comment filters."""
        env.filters['comment_count'] = self.get_comment_count
        env.filters['comments'] = self.get_comments_for_template
        
    def get_comment_count(self, post_slug: str) -> int:
        """Get comment count for post."""
        return CommentModel.select().where(
            CommentModel.post_slug == post_slug,
            CommentModel.is_approved == True,
        ).count()
        
    def get_comments_for_template(self, post_slug: str) -> List[Dict]:
        """Get comments for template."""
        comments = CommentModel.select().where(
            CommentModel.post_slug == post_slug,
            CommentModel.is_approved == True,
            CommentModel.is_spam == False,
        ).order_by(CommentModel.created_at)
        
        return [c.to_dict() for c in comments]