"""
Slides renderer for Metupy.

Renders slide presentations.
"""

from typing import Any, Dict, List


class SlidesRenderer:
    """Render slide presentations."""

    def __init__(self, engine):
        """
        Initialize SlidesRenderer.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine

    async def render_slides(self, page) -> str:
        """
        Render slides from page.

        Args:
            page: Slides page.

        Returns:
            Rendered HTML string.
        """
        slides = self._split_slides(page.content)

        context = {
            'slides': slides,
            'total_slides': len(slides),
            'presentation_title': page.title,
            'theme': page.metadata.get('theme', 'default'),
            'transition': page.metadata.get('transition', 'slide'),
        }

        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return ''

        template = template_env.get_template(
            page.metadata.get('template', 'slides.html')
        )
        return template.render(**context)

    def _split_slides(self, content: str) -> List[Dict]:
        """
        Split content into slides.

        Slides are separated by '---' on its own line.

        Args:
            content: Slide content.

        Returns:
            List of slide dictionaries.
        """
        slides = []
        parts = content.split('\n---\n')

        for i, part in enumerate(parts):
            slide = {
                'number': i + 1,
                'content': part.strip(),
                'background': None,
                'notes': None,
            }

            if '???' in part:
                slide_content, notes = part.split('???', 1)
                slide['content'] = slide_content.strip()
                slide['notes'] = notes.strip()

            slides.append(slide)

        return slides