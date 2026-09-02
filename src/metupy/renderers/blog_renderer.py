# metupy/renderers/blog_renderer.py
"""Blog Renderer."""

from typing import Dict, Any, List
from pathlib import Path

class BlogRenderer:
    """Renders blog pages."""
    
    def __init__(self, engine):
        self.engine = engine
        
    async def render_post(self, post) -> str:
        """Render single blog post."""
        context = post.get_context()
        context.update({
            'is_post': True,
            'related_posts': self._get_related_posts(post),
            'prev_post': self._get_prev_post(post),
            'next_post': self._get_next_post(post),
        })
        
        template = self.engine.template_env.get_template(
            post.metadata.get('template', 'post.html')
        )
        return template.render(**context)
        
    async def render_list(self, posts: List, page: int = 1) -> str:
        """Render blog list."""
        per_page = self.engine.config.CONTENT_TYPES['blog']['paginate']
        start = (page - 1) * per_page
        end = start + per_page
        page_posts = posts[start:end]
        
        context = {
            'posts': page_posts,
            'current_page': page,
            'total_pages': (len(posts) + per_page - 1) // per_page,
            'has_next': end < len(posts),
            'has_prev': page > 1,
        }
        
        template = self.engine.template_env.get_template('blog.html')
        return template.render(**context)
        
    async def render_archive(self, posts: List) -> str:
        """Render blog archive."""
        # Group posts by year/month
        archive = {}
        for post in posts:
            date = post.metadata.get('date', '')
            if date:
                year = date[:4]
                month = date[5:7]
                key = f"{year}-{month}"
                if key not in archive:
                    archive[key] = []
                archive[key].append(post)
                
        context = {
            'archive': archive,
        }
        
        template = self.engine.template_env.get_template('archive.html')
        return template.render(**context)
        
    def _get_related_posts(self, post, limit: int = 3) -> List:
        """Get related posts."""
        tags = post.metadata.get('tags', [])
        if not tags:
            return []
            
        related = []
        for other in self.engine.content_manager.posts:
            if other.id != post.id:
                other_tags = other.metadata.get('tags', [])
                if any(tag in other_tags for tag in tags):
                    related.append(other)
                    if len(related) >= limit:
                        break
                        
        return related
        
    def _get_prev_post(self, post):
        """Get previous post."""
        posts = self.engine.content_manager.posts
        index = next((i for i, p in enumerate(posts) if p.id == post.id), -1)
        return posts[index - 1] if index > 0 else None
        
    def _get_next_post(self, post):
        """Get next post."""
        posts = self.engine.content_manager.posts
        index = next((i for i, p in enumerate(posts) if p.id == post.id), -1)
        return posts[index + 1] if index < len(posts) - 1 else None