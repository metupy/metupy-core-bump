# metupy/renderers/docs_renderer.py
"""Documentation Renderer."""

from typing import Dict, Any, List
from pathlib import Path

class DocsRenderer:
    """Renders documentation pages."""
    
    def __init__(self, engine):
        self.engine = engine
        
    async def render_doc(self, page) -> str:
        """Render single documentation page."""
        context = page.get_context()
        context.update({
            'is_doc': True,
            'toc': self._extract_toc(page.content),
            'sidebar': self._build_sidebar(page),
            'breadcrumbs': self._build_breadcrumbs(page),
        })
        
        template = self.engine.template_env.get_template(
            page.metadata.get('template', 'docs.html')
        )
        return template.render(**context)
        
    def _extract_toc(self, content: str) -> List[Dict]:
        """Extract table of contents."""
        return self.engine.markdown_parser.extract_toc(content)
        
    def _build_sidebar(self, current_page) -> List[Dict]:
        """Build sidebar navigation."""
        docs = self.engine.content_manager.get_pages_by_type('docs')
        
        sidebar = []
        for doc in docs:
            item = {
                'title': doc.title,
                'url': doc.url,
                'current': doc.id == current_page.id,
                'children': [],
            }
            sidebar.append(item)
            
        return sidebar
        
    def _build_breadcrumbs(self, page) -> List[Dict]:
        """Build breadcrumbs."""
        breadcrumbs = [
            {'title': 'Home', 'url': '/'},
            {'title': 'Docs', 'url': '/docs/'},
        ]
        
        if page.metadata.get('section'):
            breadcrumbs.append({
                'title': page.metadata['section'],
                'url': f"/docs/{page.metadata['section']}/",
            })
            
        breadcrumbs.append({
            'title': page.title,
            'url': page.url,
        })
        
        return breadcrumbs