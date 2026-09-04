"""
Markdown parser for Metupy.

Provides enhanced markdown parsing with custom extensions.
"""

import re
from typing import Any, Dict, List, Optional

import markdown


class MetupyMarkdownParser:
    """Enhanced markdown parser for Metupy."""

    def __init__(self, engine):
        """
        Initialize markdown parser.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.extensions = getattr(engine.config, 'MARKDOWN_EXTENSIONS', ['extra', 'tables', 'fenced_code'])
        self.extension_configs = getattr(engine.config, 'MARKDOWN_EXTENSION_CONFIGS', {})
        self.md = self._create_instance()

    def _create_instance(self) -> markdown.Markdown:
        """
        Create markdown instance with extensions.

        Returns:
            Configured Markdown instance.
        """
        return markdown.Markdown(
            extensions=self.extensions,
            extension_configs=self.extension_configs,
            output_format='html5',
        )

    def convert(self, content: str) -> str:
        """
        Convert markdown to HTML.

        Args:
            content: Markdown content string.

        Returns:
            HTML string.
        """
        if not content:
            return ''

        self.md.reset()
        return self.md.convert(content)

    def strip_markdown(self, content: str) -> str:
        """
        Remove markdown syntax and return plain text.

        Args:
            content: Markdown content.

        Returns:
            Plain text without markdown syntax.
        """
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        content = re.sub(r'`.*?`', '', content)
        content = re.sub(r'#{1,6}\s*', '', content)
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
        content = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', content)
        content = re.sub(r'^\s*>\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*[-+*]\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    def extract_toc(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract table of contents from markdown.

        Args:
            content: Markdown content.

        Returns:
            List of TOC entries with level, title, and anchor.
        """
        toc = []
        pattern = r'^(#{1,6})\s+(.*?)$'

        for match in re.finditer(pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()

            anchor = title.lower()
            anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
            anchor = anchor.replace(' ', '-')

            toc.append({
                'level': level,
                'title': title,
                'anchor': anchor,
            })

        return toc

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from markdown content.

        Args:
            content: Markdown content.

        Returns:
            Dictionary with tags, links, and images.
        """
        metadata = {}

        tags = re.findall(r'#(\w+)', content)
        if tags:
            metadata['tags'] = list(set(tags))

        links = re.findall(r'\[(.*?)\]\((.*?)\)', content)
        if links:
            metadata['links'] = [{'text': text, 'url': url} for text, url in links]

        images = re.findall(r'!\[(.*?)\]\((.*?)\)', content)
        if images:
            metadata['images'] = [{'alt': alt, 'src': src} for alt, src in images]

        return metadata