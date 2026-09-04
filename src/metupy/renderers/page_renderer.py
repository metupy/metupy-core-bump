"""
Page renderer for Metupy.

Renders pages to HTML using Jinja2 templates.
"""

import markdown as md
from typing import Any, Dict, Optional


class PageRenderer:
    """Render pages to HTML."""

    def __init__(self, engine):
        """
        Initialize PageRenderer.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine

    async def render(self, page, context: Optional[Dict] = None) -> str:
        """
        Render page to HTML.

        Args:
            page: Page instance to render.
            context: Optional rendering context override.

        Returns:
            Rendered HTML string.
        """
        render_context = page.get_context()

        if context:
            render_context.update(context)

        if page.content_type in ['pym', 'markdown']:
            render_context['content'] = md.markdown(
                page.content,
                extensions=['extra', 'tables', 'fenced_code']
            )

        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return render_context.get('content', '')

        template = template_env.get_template(page.template)
        return template.render(**render_context)