"""
Page manager for Metupy.

Loads and manages Python-based pages from the pages directory.
"""

import importlib.util
import inspect
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from metupy.core.page import Page


class PageManager:
    """Manage Python-based pages for Metupy engine."""

    def __init__(self, engine):
        """
        Initialize PageManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.pages: List[Page] = []
        self.page_index: Dict[str, Page] = {}
        self.python_pages: List[Page] = []

    async def load_pages(self) -> None:
        """Load all Python pages from pages directory."""
        pages_dir = self.engine.base_dir / 'pages'

        if not pages_dir.exists():
            return

        for page_file in pages_dir.rglob('*.py'):
            if page_file.name.startswith('_'):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"metupy_page_{page_file.stem}",
                    page_file
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Page) and obj != Page:
                        page_instance = obj(self.engine)
                        page_instance.id = str(uuid.uuid4())
                        page_instance.source_file = page_file
                        page_instance.is_python_page = True
                        self.pages.append(page_instance)
                        self.python_pages.append(page_instance)
                        print(f"  Loaded Python page: {page_file.stem}")

            except Exception as e:
                print(f"  Error loading page {page_file}: {e}")

        self._build_index()

    def _build_index(self) -> None:
        """Build page index by ID."""
        self.page_index.clear()
        for page in self.pages:
            self.page_index[page.id] = page

    def get_page(self, page_id: str) -> Optional[Page]:
        """
        Get page by ID.

        Args:
            page_id: Page identifier.

        Returns:
            Page instance or None.
        """
        return self.page_index.get(page_id)

    def get_all_pages(self) -> List[Page]:
        """
        Get all pages.

        Returns:
            List of all pages.
        """
        return self.pages

    def get_python_pages(self) -> List[Page]:
        """
        Get Python-based pages.

        Returns:
            List of Python pages.
        """
        return self.python_pages

    def add_page(self, page: Page) -> None:
        """
        Add page to manager.

        Args:
            page: Page instance to add.
        """
        if not page.id:
            page.id = str(uuid.uuid4())
        self.pages.append(page)
        self.page_index[page.id] = page

    def remove_page(self, page_id: str) -> None:
        """
        Remove page from manager.

        Args:
            page_id: Page identifier to remove.
        """
        if page_id in self.page_index:
            page = self.page_index[page_id]
            self.pages.remove(page)
            if page in self.python_pages:
                self.python_pages.remove(page)
            del self.page_index[page_id]

    def get_page_stats(self) -> Dict[str, Any]:
        """
        Get page statistics.

        Returns:
            Dictionary with page counts.
        """
        return {
            'total_pages': len(self.pages),
            'python_pages': len(self.python_pages),
        }

    def clear(self) -> None:
        """Clear all pages from memory."""
        self.pages.clear()
        self.page_index.clear()
        self.python_pages.clear()

    async def reload(self) -> None:
        """Reload all pages from disk."""
        self.clear()
        await self.load_pages()