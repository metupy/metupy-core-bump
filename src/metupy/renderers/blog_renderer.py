"""
Blog renderer for Metupy.

Renders blog posts and listings.
"""

from typing import Any, Dict, List, Optional


class BlogRenderer:
    """Render blog pages."""

    def __init__(self, engine):
        """
        Initialize BlogRenderer.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine

    async def render_post(self, post) -> str:
        """
        Render single blog post.

        Args:
            post: Blog post page.

        Returns:
            Rendered HTML string.
        """
        context = post.get_context()

        context.update({
            'is_post': True,
            'related_posts': self._get_related_posts(post),
            'prev_post': self._get_prev_post(post),
            'next_post': self._get_next_post(post),
        })

        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return context.get('content', '')

        template = template_env.get_template(
            post.metadata.get('template', 'post.html')
        )
        return template.render(**context)

    async def render_list(self, posts: List, page: int = 1) -> str:
        """
        Render blog post listing.

        Args:
            posts: List of posts.
            page: Page number.

        Returns:
            Rendered HTML string.
        """
        per_page = 10
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

        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return ''

        template = template_env.get_template('blog.html')
        return template.render(**context)

    def _get_related_posts(self, post, limit: int = 3) -> List:
        """
        Get related posts by tags.

        Args:
            post: Current post.
            limit: Maximum related posts.

        Returns:
            List of related posts.
        """
        tags = post.metadata.get('tags', [])
        if not tags:
            return []

        content_manager = getattr(self.engine, 'content_manager', None)
        if not content_manager:
            return []

        related = []
        for other in content_manager.posts:
            if other.id == post.id:
                continue
            other_tags = other.metadata.get('tags', [])
            if any(tag in other_tags for tag in tags):
                related.append(other)
                if len(related) >= limit:
                    break

        return related

    def _get_prev_post(self, post):
        """Get previous post."""
        content_manager = getattr(self.engine, 'content_manager', None)
        if not content_manager:
            return None

        posts = content_manager.posts
        index = next((i for i, p in enumerate(posts) if p.id == post.id), -1)
        return posts[index - 1] if index > 0 else None

    def _get_next_post(self, post):
        """Get next post."""
        content_manager = getattr(self.engine, 'content_manager', None)
        if not content_manager:
            return None

        posts = content_manager.posts
        index = next((i for i, p in enumerate(posts) if p.id == post.id), -1)
        return posts[index + 1] if index < len(posts) - 1 else None