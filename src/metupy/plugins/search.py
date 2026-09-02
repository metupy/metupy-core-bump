# metupy/plugins/search.py
"""Search Plugin - Add search functionality."""

from metupy.core.plugin_manager import MetupyPlugin
from typing import Dict, Any, List
from pathlib import Path
import json

class SearchPlugin(MetupyPlugin):
    """Search plugin for Metupy."""
    
    name = "search"
    version = "1.0.0"
    description = "Add search functionality to your site"
    author = "Metupy Team"
    url = "https://metupy.dev/plugins/search"
    
    def __init__(self, engine):
        super().__init__(engine)
        self.search_config = {}
        self.search_index = {}
        
    def setup(self):
        """Setup search plugin."""
        self.search_config = self.engine.config.SEARCH
        print(f"Search Plugin v{self.version} initialized")
        
    def on_build_end(self, engine):
        """Generate search index after build."""
        self._generate_search_index()
        
    def _generate_search_index(self):
        """Generate search index."""
        index = []
        
        for page in self.engine.content_manager.pages:
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
            
        # Write index
        index_path = self.engine.output_dir / 'search-index.json'
        index_path.write_text(json.dumps(index))
        
        # Generate search script
        search_script = self._generate_search_script()
        script_path = self.engine.output_dir / 'search.js'
        script_path.write_text(search_script)
        
        print(f"Search index generated: {index_path}")
        
    def _extract_text(self, html_content: str) -> str:
        """Extract text from HTML."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
        
    def _generate_search_script(self) -> str:
        """Generate search JavaScript."""
        return """// Metupy Search
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
                results.push({
                    ...item,
                    score: score,
                });
            }
        }
        
        return results.sort((a, b) => b.score - a.score);
    }
    
    calculateScore(item, query) {
        let score = 0;
        
        // Check title
        if (item.title.toLowerCase().includes(query)) {
            score += 10;
        }
        
        // Check description
        if (item.description.toLowerCase().includes(query)) {
            score += 5;
        }
        
        // Check content
        if (item.content.includes(query)) {
            score += 2;
        }
        
        // Check tags
        for (const tag of item.tags) {
            if (tag.toLowerCase().includes(query)) {
                score += 3;
            }
        }
        
        return score;
    }
}

// Initialize search
window.metupySearch = new MetupySearch();
"""
        
    def setup_routes(self, app):
        """Setup search API routes."""
        from aiohttp import web
        
        async def search_api(request):
            query = request.query.get('q', '')
            results = self.search(query)
            return web.json_response(results)
            
        app.router.add_get('/api/search', search_api)
        
    def search(self, query: str) -> List[Dict]:
        """Search content."""
        results = []
        query = query.lower()
        
        for page in self.engine.content_manager.pages:
            score = 0
            
            # Check title
            if query in page.title.lower():
                score += 10
                
            # Check content
            if query in self._extract_text(page.content):
                score += 5
                
            # Check tags
            for tag in page.metadata.get('tags', []):
                if query in tag.lower():
                    score += 3
                    
            if score > 0:
                results.append({
                    'title': page.title,
                    'url': page.url,
                    'description': page.metadata.get('description', ''),
                    'score': score,
                })
                
        return sorted(results, key=lambda x: x['score'], reverse=True)