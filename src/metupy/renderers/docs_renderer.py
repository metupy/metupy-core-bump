"""
Documentation renderer for Metupy.

Renders documentation pages with TOC and sidebar.
"""

from typing import Any, Dict, List, Optional


class DocsRenderer:
    """Render documentation pages."""

    def __init__(self, engine):
        """
        Initialize DocsRenderer.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine

    async def render_doc(self, page) -> str:
        """
        Render documentation page.

        Args:
            page: Documentation page.

        Returns:
            Rendered HTML string.
        """
        context = page.get_context()

        context.update({
            'is_doc': True,
            'toc': self._extract_toc(page.content),
            'sidebar': self._build_sidebar(page),
            'breadcrumbs': self._build_breadcrumbs(page),
        })

        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return context.get('content', '')

        template = template_env.get_template(
            page.metadata.get('template', 'docs.html')
        )
        return template.render(**context)

    def _extract_toc(self, content: str) -> List[Dict]:
        """
        Extract table of contents from content.

        Args:
            content: Markdown content.

        Returns:
            List of TOC entries.
        """
        markdown_parser = getattr(self.engine, 'markdown_parser', None)
        if markdown_parser and hasattr(markdown_parser, 'extract_toc'):
            return markdown_parser.extract_toc(content)
        return []

    def _build_sidebar(self, current_page) -> List[Dict]:
        """
        Build sidebar navigation.

        Args:
            current_page: Current page.

        Returns:
            List of sidebar items.
        """
        content_manager = getattr(self.engine, 'content_manager', None)
        if not content_manager:
            return []

        docs = content_manager.get_pages_by_type('docs')

        sidebar = []
        for doc in docs:
            sidebar.append({
                'title': doc.title,
                'url': doc.url,
                'current': doc.id == current_page.id,
                'children': [],
            })

        return sidebar

    def _build_breadcrumbs(self, page) -> List[Dict]:
        """
        Build breadcrumb navigation.

        Args:
            page: Current page.

        Returns:
            List of breadcrumb items.
        """
        breadcrumbs = [
            {'title': 'Home', 'url': '/'},
            {'title': 'Docs', 'url': '/docs/'},
        ]

        section = page.metadata.get('section')
        if section:
            breadcrumbs.append({
                'title': section,
                'url': f"/docs/{section.lower().replace(' ', '-')}/",
            })

        breadcrumbs.append({
            'title': page.title,
            'url': page.url,
        })

        return breadcrumbs