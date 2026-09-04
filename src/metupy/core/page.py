"""
Page system for Metupy.

Defines base Page class and specialized page types for
Markdown, PYM, and Python content files.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from metupy.utils.helpers import read_file, slugify


class Page:
    """Base Page class for all Metupy pages."""

    title: str = "Untitled"
    template: str = "layout.html"
    content_type: str = "page"
    is_post: bool = False
    output_path: str = "index.html"

    def __init__(self, engine, **kwargs):
        """
        Initialize Page instance.

        Args:
            engine: MetupyEngine instance.
            **kwargs: Page attributes.
        """
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
        """
        Get page rendering context.

        Returns:
            Dictionary of context variables for template rendering.
        """
        context = {
            'page': self,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata or {},
            'url': self.url,
            'engine': self.engine,
            'now': datetime.now(),
        }

        if hasattr(self.engine, 'site_context'):
            context['site'] = self.engine.site_context

        if hasattr(self.engine, 'navigation'):
            context['nav'] = self.engine.navigation

        context.update(self.context)
        return context

    def render(self, template_env=None) -> str:
        """
        Render page to HTML.

        Args:
            template_env: Optional Jinja2 environment override.

        Returns:
            Rendered HTML string.
        """
        env = template_env or getattr(self.engine, 'template_env', None)
        if not env:
            return self.content

        template = env.get_template(self.template)
        context = self.get_context()
        return template.render(**context)

    def __repr__(self) -> str:
        """String representation of Page."""
        return f"<Page {self.title}>"


class MarkdownPage(Page):
    """Page type for .md markdown files."""

    content_type = "markdown"

    @classmethod
    async def from_file(cls, engine, file_path: Path) -> 'MarkdownPage':
        """
        Create MarkdownPage from file.

        Args:
            engine: MetupyEngine instance.
            file_path: Path to .md file.

        Returns:
            MarkdownPage instance.
        """
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
                except (yaml.YAMLError, ValueError):
                    pass

        slug = file_path.stem

        if file_path.name == 'index.md':
            parent = file_path.parent.name
            output_path = "index.html" if parent == "content" else f"{parent}/index.html"
        else:
            output_path = f"{slug}/index.html"

        return cls(
            engine,
            id=slug,
            title=metadata.get('title', slug.replace('-', ' ').title()),
            template=metadata.get('template', 'layout.html'),
            metadata=metadata,
            content=body,
            source_file=file_path,
            url=metadata.get('url', f"/{slug}/"),
            output_path=output_path,
        )


class PYMPage(Page):
    """Page type for .pym files (Python + Markdown + Jinja2)."""

    content_type = "pym"

    @classmethod
    async def from_file(cls, engine, file_path: Path) -> 'PYMPage':
        """
        Create PYMPage from .pym file.

        Args:
            engine: MetupyEngine instance.
            file_path: Path to .pym file.

        Returns:
            PYMPage instance.
        """
        content = read_file(file_path)

        metadata = {}
        body = content
        context = {}

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                except (yaml.YAMLError, ValueError):
                    pass

        # Optional Python blocks (```pym ... ```) will be processed later
        # by the engine if a Pyodide/Node.js executor is available.
        # For now, we keep the raw body as markdown content.
        slug = file_path.stem

        if file_path.name == 'index.pym':
            parent = file_path.parent.name
            if parent in ("content", "docs"):
                output_path = "index.html"
            else:
                output_path = f"{parent}/index.html"
        else:
            output_path = f"{slug}/index.html"

        page = cls(
            engine,
            id=slug,
            title=metadata.get('title', slug.replace('-', ' ').title()),
            template=metadata.get('template', 'layout.html'),
            metadata=metadata,
            content=body,
            context=context,
            source_file=file_path,
            url=metadata.get('url', f"/{slug}/"),
            output_path=output_path,
        )

        if 'date' in metadata:
            page.is_post = True

        return page


class PythonPage(Page):
    """
    Page type for .py files.

    The .py file should define either a `page` object with
    attributes title, content, template, or a `context` dict.
    """

    content_type = "python"

    @classmethod
    async def from_file(cls, engine, file_path: Path) -> 'PythonPage':
        """
        Create PythonPage from file.

        Args:
            engine: MetupyEngine instance.
            file_path: Path to .py file.

        Returns:
            PythonPage instance.
        """
        namespace = {'engine': engine, 'site': getattr(engine, 'site_context', {})}
        code = read_file(file_path)
        exec(code, namespace)

        # Extract page object or context
        page_obj = namespace.get('page')
        context_dict = namespace.get('context', {})

        title = getattr(page_obj, 'title', file_path.stem.replace('_', ' ').title()) if page_obj else context_dict.get('title', file_path.stem.replace('_', ' ').title())
        template = getattr(page_obj, 'template', 'layout.html') if page_obj else context_dict.get('template', 'layout.html')
        content = getattr(page_obj, 'content', '') if page_obj else context_dict.get('content', '')
        metadata = getattr(page_obj, 'metadata', {}) if page_obj else context_dict.get('metadata', {})

        slug = file_path.stem
        if file_path.name == 'index.py':
            output_path = "index.html"
        else:
            output_path = f"{slug}/index.html"

        return cls(
            engine,
            id=slug,
            title=title,
            template=template,
            metadata=metadata,
            content=content,
            source_file=file_path,
            url=metadata.get('url', f"/{slug}/"),
            output_path=output_path,
            context=context_dict,
            is_python_page=True,
        )