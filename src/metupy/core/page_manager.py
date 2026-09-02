# metupy/core/page_manager.py
"""Page Manager untuk Metupy."""

from pathlib import Path
from typing import Dict, List, Any, Optional, Type
import asyncio
import importlib.util
import inspect
import sys
import uuid

from metupy.core.page import Page, MarkdownPage, PYMPage

class PageManager:
    """Manages pages for Metupy."""
    
    def __init__(self, engine):
        self.engine = engine
        self.pages: List[Page] = []
        self.page_index: Dict[str, Page] = {}
        self.python_pages: List[Page] = []
        self.content_pages: List[Page] = []
        
    async def load_pages(self):
        """Load all pages."""
        pages_dir = self.engine.base_dir / 'pages'
        
        if not pages_dir.exists():
            return
            
        # Load Python pages
        await self._load_python_pages(pages_dir)
        
        # Build index
        self._build_index()
        
    async def _load_python_pages(self, pages_dir: Path):
        """Load Python page files."""
        for page_file in pages_dir.rglob('*.py'):
            if page_file.name.startswith('_'):
                continue
                
            try:
                # Import page module
                spec = importlib.util.spec_from_file_location(
                    f"metupy_page_{page_file.stem}",
                    page_file
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                # Find Page classes
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Page):
                        if obj != Page:
                            page_instance = obj(self.engine)
                            page_instance.id = str(uuid.uuid4())
                            page_instance.source_file = page_file
                            page_instance.is_python_page = True
                            self.pages.append(page_instance)
                            self.python_pages.append(page_instance)
                            print(f"  Loaded Python page: {page_file.stem}")
                            
            except Exception as e:
                print(f"  Error loading page {page_file}: {e}")
                
    def _build_index(self):
        """Build page index."""
        self.page_index.clear()
        for page in self.pages:
            self.page_index[page.id] = page
            
    def get_page(self, page_id: str) -> Optional[Page]:
        """Get page by ID."""
        return self.page_index.get(page_id)
        
    def get_page_by_title(self, title: str) -> Optional[Page]:
        """Get page by title."""
        for page in self.pages:
            if page.title == title:
                return page
        return None
        
    def get_pages_by_type(self, content_type: str) -> List[Page]:
        """Get pages by type."""
        return [
            page for page in self.pages
            if getattr(page, 'content_type', 'page') == content_type
        ]
        
    def get_all_pages(self) -> List[Page]:
        """Get all pages."""
        return self.pages
        
    def get_python_pages(self) -> List[Page]:
        """Get Python pages."""
        return self.python_pages
        
    def add_page(self, page: Page):
        """Add page."""
        if not page.id:
            page.id = str(uuid.uuid4())
        self.pages.append(page)
        self.page_index[page.id] = page
        
    def remove_page(self, page_id: str):
        """Remove page."""
        if page_id in self.page_index:
            page = self.page_index[page_id]
            self.pages.remove(page)
            del self.page_index[page_id]
            if page in self.python_pages:
                self.python_pages.remove(page)
                
    def clear(self):
        """Clear all pages."""
        self.pages.clear()
        self.page_index.clear()
        self.python_pages.clear()
        
    async def reload(self):
        """Reload all pages."""
        self.clear()
        await self.load_pages()
        
    def get_page_stats(self) -> Dict[str, Any]:
        """Get page statistics."""
        return {
            'total_pages': len(self.pages),
            'python_pages': len(self.python_pages),
            'content_pages': len(self.content_pages),
        }