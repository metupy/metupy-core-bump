# metupy/core/page.py
"""Page System untuk Metupy."""

from pathlib import Path
from typing import Dict, Any, Optional
from metupy.utils.helpers import slugify, read_file


class Page:
    """Base Page class."""
    
    title: str = "Untitled"
    template: str = "default.html"
    content_type: str = "page"
    is_post: bool = False
    output_path: str = "index.html"
    
    def __init__(self, engine, **kwargs):
        self.engine = engine
        self.id = kwargs.get('id', slugify(self.title))
        self.title = kwargs.get('title', self.title)
        self.template = kwargs.get('template', self.template)
        self.metadata = kwargs.get('metadata', {})
        self.context = kwargs.get('context', {})
        self.content = kwargs.get('content', '')
        self.source_file = kwargs.get('source_file', None)
        self.url = kwargs.get('url', '/')
        self.output_path = kwargs.get('output_path', 'index.html')
        self.is_python_page = False
        
    def get_context(self) -> Dict[str, Any]:
        """Get page context."""
        context = {
            'page': self,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata or {},  # Always ensure metadata exists
            'url': self.url,
            'engine': self.engine,
        }
        if hasattr(self.engine, 'site_context'):
            context['site'] = self.engine.site_context
        # Add now for templates
        context['now'] = __import__('datetime').datetime.now()
        # Add custom context
        context.update(self.context)
        return context
        
    def render(self, template_env=None) -> str:
        """Render page to HTML."""
        env = template_env or getattr(self.engine, 'template_env', None)
        if not env:
            return self.content
            
        template = env.get_template(self.template)
        context = self.get_context()
        return template.render(**context)
        
    def __repr__(self):
        return f"<Page {self.title}>"


class MarkdownPage(Page):
    """Page for Markdown files."""
    
    content_type = "markdown"
    
    @classmethod
    async def from_file(cls, engine, file_path: Path) -> 'MarkdownPage':
        """Create page from markdown file."""
        content = read_file(file_path)
        
        metadata = {}
        body = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                except Exception:
                    pass
                    
        slug = file_path.stem
        if file_path.name == 'index.md':
            parent = file_path.parent.name
            if parent == 'content':
                output_path = "index.html"
            else:
                output_path = f"{parent}/index.html"
        else:
            output_path = f"{slug}/index.html"
            
        return cls(
            engine,
            id=slug,
            title=metadata.get('title', slug.replace('-', ' ').title()),
            template=metadata.get('template', 'default.html'),
            metadata=metadata,
            content=body,
            source_file=file_path,
            url=metadata.get('url', f"/{slug}/"),
            output_path=output_path,
        )


class PYMPage(Page):
    """Page for .pym files."""
    
    content_type = "pym"
    
    @classmethod
    async def from_file(cls, engine, file_path: Path) -> 'PYMPage':
        """Create page from .pym file."""
        content = read_file(file_path)
        
        metadata = {}
        body = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                except Exception:
                    pass
                    
        slug = file_path.stem
        if file_path.name == 'index.pym':
            parent = file_path.parent.name
            if parent == 'content':
                output_path = "index.html"
            else:
                output_path = f"{parent}/index.html"
        else:
            output_path = f"{slug}/index.html"
            
        page = cls(
            engine,
            id=slug,
            title=metadata.get('title', slug.replace('-', ' ').title()),
            template=metadata.get('template', 'default.html'),
            metadata=metadata,
            content=body,
            source_file=file_path,
            url=metadata.get('url', f"/{slug}/"),
            output_path=output_path,
        )
        
        if 'date' in metadata:
            page.is_post = True
            
        return page