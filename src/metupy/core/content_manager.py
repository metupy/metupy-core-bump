"""
Content manager for Metupy.

Loads and manages all content files, builds navigation,
and provides template context similar to MkDocs.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from metupy.core.page import Page, MarkdownPage, PYMPage, PythonPage


class ContentManager:
    """Manage all content files for Metupy engine."""

    def __init__(self, engine):
        """
        Initialize ContentManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.pages: List[Page] = []
        self.posts: List[Page] = []
        self.collections: Dict[str, List[Page]] = {}
        self.navigation: List[Dict[str, Any]] = []

    async def load_content(self) -> None:
        """Load all content from content directory."""
        content_dir = self.engine.content_dir

        if not content_dir.exists():
            return

        await self._load_files(content_dir)
        self._sort_pages()
        self._build_navigation()

    async def _load_files(self, directory: Path) -> None:
        """Load supported files recursively."""
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                if file_path.suffix == '.pym':
                    page = await PYMPage.from_file(self.engine, file_path)
                elif file_path.suffix == '.py' and 'templates' not in file_path.parts:
                    page = await PythonPage.from_file(self.engine, file_path)
                elif file_path.suffix == '.md':
                    page = await MarkdownPage.from_file(self.engine, file_path)
                else:
                    continue
                self._add_page(page)

    def _add_page(self, page: Page) -> None:
        """Add page to collections."""
        self.pages.append(page)
        if page.is_post:
            self.posts.append(page)

        content_type = page.metadata.get('type', 'docs')
        self.collections.setdefault(content_type, []).append(page)

    def _sort_pages(self) -> None:
        """Sort pages by order metadata then title."""
        for collection in self.collections.values():
            collection.sort(key=lambda p: (p.metadata.get('order', 9999), p.title))

    def _build_navigation(self) -> None:
        """Build navigation structure from pages."""
        docs = self.collections.get('docs', self.pages)
        self.navigation = []
        for page in docs:
            self.navigation.append({
                'title': page.title,
                'url': page.url,
                'active': False,
            })

    def get_docs_sidebar(self, current_page: Optional[Page] = None) -> List[Dict[str, Any]]:
        """
        Build sidebar groups for documentation pages.

        Args:
            current_page: Current page to mark active.

        Returns:
            List of group dictionaries.
        """
        docs = self.collections.get('docs', self.pages)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for page in docs:
            section = page.metadata.get('section', 'Documentation')
            item = {
                'title': page.title,
                'url': page.url,
                'current': current_page is not None and page.id == current_page.id,
                'is_folder': False,
                'children': [],
            }
            groups.setdefault(section, []).append(item)
        return [{'title': section, 'items': items} for section, items in groups.items()]

    def get_toc_items(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract TOC items from page markdown content.

        Args:
            page: Page instance.

        Returns:
            List of TOC entries.
        """
        toc = []
        for match in re.finditer(r'^(#{2,3})\s+(.*?)\s*$', page.content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            anchor = title.lower()
            anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
            anchor = anchor.replace(' ', '-')
            toc.append({'level': level, 'title': title, 'anchor': anchor})
        return toc

    def get_prev_next_docs(self, page: Page):
        """Return previous and next documentation pages."""
        docs = self.collections.get('docs', self.pages)
        index = next((i for i, d in enumerate(docs) if d.id == page.id), -1)
        prev_doc = docs[index - 1] if index > 0 else None
        next_doc = docs[index + 1] if index >= 0 and index < len(docs) - 1 else None
        return prev_doc, next_doc

    def get_page_by_id(self, page_id: str) -> Optional[Page]:
        for page in self.pages:
            if page.id == page_id:
                return page
        return None

    def get_pages_by_type(self, content_type: str) -> List[Page]:
        return self.collections.get(content_type, [])

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_pages': len(self.pages),
            'total_posts': len(self.posts),
            'collections': {name: len(pages) for name, pages in self.collections.items()},
        }

    def clear(self) -> None:
        self.pages.clear()
        self.posts.clear()
        self.collections.clear()
        self.navigation.clear()

    async def reload(self) -> None:
        self.clear()
        await self.load_content()