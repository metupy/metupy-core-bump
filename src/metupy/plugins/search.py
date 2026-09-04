"""
Search plugin for Metupy.

Provides search functionality for site content.
Generates search index during build.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from metupy.core.plugin_manager import MetupyPlugin


class SearchPlugin(MetupyPlugin):
    """Search functionality plugin."""

    name = "search"
    version = "1.0.0"
    description = "Add search functionality to your site"
    author = "Metupy Team"

    def __init__(self, engine):
        """Initialize search plugin."""
        super().__init__(engine)
        self.search_config = {}

    def setup(self) -> None:
        """Setup search plugin."""
        self.search_config = getattr(self.engine.config, 'SEARCH', {})
        print(f"  Search Plugin v{self.version} loaded")

    def on_build_end(self, engine) -> None:
        """Generate search index after build."""
        if not self.search_config.get('enabled', True):
            return

        self._generate_search_index()

    def _generate_search_index(self) -> None:
        """Generate search index JSON file."""
        index = []

        content_manager = getattr(self.engine, 'content_manager', None)
        page_manager = getattr(self.engine, 'page_manager', None)

        all_pages = []

        if content_manager:
            all_pages.extend(content_manager.pages)

        if page_manager:
            all_pages.extend(page_manager.pages)

        for page in all_pages:
            entry = {
                'id': page.id,
                'title': page.title,
                'url': page.url,
                'description': page.metadata.get('description', ''),
                'content': self._extract_text(page.content),
                'tags': page.metadata.get('tags', []),
                'type': page.metadata.get('type', 'page'),
            }
            index.append(entry)

        index_path = self.engine.output_dir / 'search-index.json'
        index_path.write_text(
            json.dumps(index, ensure_ascii=False),
            encoding='utf-8'
        )

        search_js = self._generate_search_script()
        script_path = self.engine.output_dir / 'search.js'
        script_path.write_text(search_js, encoding='utf-8')

        print(f"  Search index generated: {index_path}")

    def _extract_text(self, content: str) -> str:
        """
        Extract plain text from HTML.

        Args:
            content: HTML content.

        Returns:
            Plain text.
        """
        import re
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def _generate_search_script(self) -> str:
        """
        Generate client-side search script.

        Returns:
            JavaScript code string.
        """
        return """
// Metupy Search
class MetupySearch {
    constructor() {
        this.index = [];
        this.loadIndex();
    }

    async loadIndex() {
        try {
            const response = await fetch('/search-index.json');
            this.index = await response.json();
        } catch (error) {
            console.error('Failed to load search index:', error);
        }
    }

    search(query) {
        query = query.toLowerCase();
        const results = [];

        for (const item of this.index) {
            const score = this.calculateScore(item, query);
            if (score > 0) {
                results.push({ ...item, score: score });
            }
        }

        return results.sort((a, b) => b.score - a.score);
    }

    calculateScore(item, query) {
        let score = 0;

        if (item.title.toLowerCase().includes(query)) {
            score += 10;
        }

        if (item.description.toLowerCase().includes(query)) {
            score += 5;
        }

        if (item.content.includes(query)) {
            score += 2;
        }

        for (const tag of item.tags) {
            if (tag.toLowerCase().includes(query)) {
                score += 3;
            }
        }

        return score;
    }
}

window.metupySearch = new MetupySearch();
"""