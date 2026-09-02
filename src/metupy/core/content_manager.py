# metupy/core/content_manager.py
"""Content Manager - Mengelola semua konten Metupy."""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import re
import json

from metupy.core.page import Page, MarkdownPage, PYMPage
from metupy.utils.helpers import slugify, read_file

class ContentManager:
    """Manages all content for Metupy."""
    
    def __init__(self, engine):
        self.engine = engine
        self.pages: List[Page] = []
        self.posts: List[Page] = []
        self.collections: Dict[str, List[Page]] = {}
        self.content_index: Dict[str, Dict] = {}
        self.tag_index: Dict[str, List[Page]] = {}
        self.category_index: Dict[str, List[Page]] = {}
        
    async def load_content(self):
        """Load all content from content directory."""
        content_dir = self.engine.content_dir
        
        if not content_dir.exists():
            print(f"Content directory not found: {content_dir}")
            return
            
        # Load .pym files
        await self._load_pym_files(content_dir)
        
        # Load .md files
        await self._load_markdown_files(content_dir)
        
        # Build indexes
        self._build_indexes()
        
        # Sort content
        self._sort_content()
        
    async def _load_pym_files(self, directory: Path):
        """Load .pym files."""
        for pym_file in directory.rglob('*.pym'):
            # Skip template files
            if 'templates' in pym_file.parts:
                continue
                
            try:
                page = await PYMPage.from_file(self.engine, pym_file)
                self._add_page(page)
                print(f"  Loaded: {pym_file.relative_to(self.engine.content_dir)}")
            except Exception as e:
                print(f"  Error loading {pym_file}: {e}")
                
    async def _load_markdown_files(self, directory: Path):
        """Load .md files."""
        for md_file in directory.rglob('*.md'):
            try:
                page = await MarkdownPage.from_file(self.engine, md_file)
                self._add_page(page)
                print(f"  Loaded: {md_file.relative_to(self.engine.content_dir)}")
            except Exception as e:
                print(f"  Error loading {md_file}: {e}")
                
    def _add_page(self, page: Page):
        """Add page to collections."""
        # Add to pages list
        self.pages.append(page)
        
        # Add to posts if it's a blog post
        if page.is_post or page.metadata.get('type') == 'post':
            self.posts.append(page)
            
        # Add to collection based on type
        content_type = page.metadata.get('type', 'page')
        if content_type not in self.collections:
            self.collections[content_type] = []
        self.collections[content_type].append(page)
        
        # Add to tag index
        tags = page.metadata.get('tags', [])
        for tag in tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(page)
            
        # Add to category index
        categories = page.metadata.get('categories', [])
        for category in categories:
            if category not in self.category_index:
                self.category_index[category] = []
            self.category_index[category].append(page)
            
    def _build_indexes(self):
        """Build content indexes."""
        for page in self.pages:
            self.content_index[page.id] = {
                'id': page.id,
                'title': page.title,
                'url': page.url,
                'content': self._extract_text(page.content),
                'metadata': page.metadata,
                'tags': page.metadata.get('tags', []),
                'categories': page.metadata.get('categories', []),
                'date': page.metadata.get('date', ''),
                'type': page.metadata.get('type', 'page'),
                'author': page.metadata.get('author', ''),
                'description': page.metadata.get('description', ''),
            }
            
    def _extract_text(self, html_content: str) -> str:
        """Extract plain text from HTML."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def _sort_content(self):
        """Sort content."""
        # Sort posts by date
        self.posts.sort(
            key=lambda x: x.metadata.get('date', ''),
            reverse=True
        )
        
        # Sort pages by order
        for collection in self.collections.values():
            collection.sort(
                key=lambda x: x.metadata.get('order', 0)
            )
            
    def get_page(self, page_id: str) -> Optional[Page]:
        """Get page by ID."""
        for page in self.pages:
            if page.id == page_id:
                return page
        return None
        
    def get_page_by_slug(self, slug: str) -> Optional[Page]:
        """Get page by slug."""
        for page in self.pages:
            if page.metadata.get('slug') == slug:
                return page
        return None
        
    def get_pages_by_type(self, content_type: str) -> List[Page]:
        """Get pages by type."""
        return self.collections.get(content_type, [])
        
    def get_pages_by_tag(self, tag: str) -> List[Page]:
        """Get pages by tag."""
        return self.tag_index.get(tag, [])
        
    def get_pages_by_category(self, category: str) -> List[Page]:
        """Get pages by category."""
        return self.category_index.get(category, [])
        
    def get_all_tags(self) -> List[Dict]:
        """Get all tags with counts."""
        return [
            {'name': tag, 'count': len(pages)}
            for tag, pages in self.tag_index.items()
        ]
        
    def get_all_categories(self) -> List[Dict]:
        """Get all categories with counts."""
        return [
            {'name': category, 'count': len(pages)}
            for category, pages in self.category_index.items()
        ]
        
    def search(self, query: str) -> List[Dict]:
        """Search content."""
        query = query.lower()
        results = []
        
        for page_id, data in self.content_index.items():
            score = 0
            
            # Check title
            if query in data['title'].lower():
                score += 10
                
            # Check content
            if query in data['content'].lower():
                score += 5
                
            # Check tags
            for tag in data['tags']:
                if query in tag.lower():
                    score += 3
                    
            # Check description
            if query in data['description'].lower():
                score += 2
                
            if score > 0:
                results.append({
                    **data,
                    'score': score,
                })
                
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
        
    def get_related_pages(self, page: Page, limit: int = 3) -> List[Page]:
        """Get related pages based on tags."""
        tags = page.metadata.get('tags', [])
        if not tags:
            return []
            
        related = []
        for other in self.pages:
            if other.id == page.id:
                continue
                
            other_tags = other.metadata.get('tags', [])
            if any(tag in other_tags for tag in tags):
                related.append(other)
                if len(related) >= limit:
                    break
                    
        return related
        
    def get_prev_post(self, post: Page) -> Optional[Page]:
        """Get previous post."""
        index = next((i for i, p in enumerate(self.posts) if p.id == post.id), -1)
        return self.posts[index - 1] if index > 0 else None
        
    def get_next_post(self, post: Page) -> Optional[Page]:
        """Get next post."""
        index = next((i for i, p in enumerate(self.posts) if p.id == post.id), -1)
        return self.posts[index + 1] if index < len(self.posts) - 1 else None
        
    def get_posts_by_year(self, year: int) -> List[Page]:
        """Get posts by year."""
        return [
            post for post in self.posts
            if post.metadata.get('date', '').startswith(str(year))
        ]
        
    def get_posts_by_month(self, year: int, month: int) -> List[Page]:
        """Get posts by month."""
        prefix = f"{year}-{month:02d}"
        return [
            post for post in self.posts
            if post.metadata.get('date', '').startswith(prefix)
        ]
        
    def get_archive(self) -> Dict[str, List[Page]]:
        """Get archive grouped by year/month."""
        archive = {}
        
        for post in self.posts:
            date = post.metadata.get('date', '')
            if date:
                year = date[:4]
                month = date[5:7]
                key = f"{year}-{month}"
                if key not in archive:
                    archive[key] = []
                archive[key].append(post)
                
        return archive
        
    def get_stats(self) -> Dict[str, Any]:
        """Get content statistics."""
        return {
            'total_pages': len(self.pages),
            'total_posts': len(self.posts),
            'total_tags': len(self.tag_index),
            'total_categories': len(self.category_index),
            'collections': {
                name: len(pages)
                for name, pages in self.collections.items()
            },
        }
        
    def clear(self):
        """Clear all content."""
        self.pages.clear()
        self.posts.clear()
        self.collections.clear()
        self.content_index.clear()
        self.tag_index.clear()
        self.category_index.clear()
        
    async def reload(self):
        """Reload all content."""
        self.clear()
        await self.load_content()