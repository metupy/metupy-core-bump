# metupy/plugins/seo.py
"""SEO Plugin - Optimasi SEO untuk Metupy."""

from metupy.core.plugin_manager import MetupyPlugin
from typing import Dict, Any, List
import re
from pathlib import Path
import json

class SEOPlugin(MetupyPlugin):
    """SEO optimization plugin."""
    
    name = "seo"
    version = "1.0.0"
    description = "SEO optimization for Metupy sites"
    author = "Metupy Team"
    url = "https://metupy.dev/plugins/seo"
    
    def __init__(self, engine):
        super().__init__(engine)
        self.seo_config = {}
        
    def setup(self):
        """Setup SEO plugin."""
        self.seo_config = self.engine.config.SEO
        print(f"SEO Plugin v{self.version} initialized")
        
    def on_page_before_render(self, page, context):
        """Add SEO data to page context."""
        seo_context = self._generate_seo_context(page)
        context.update(seo_context)
        return context
        
    def on_page_after_render(self, page, html):
        """Add SEO meta tags to rendered page."""
        if not self.seo_config.get('generate_meta', True):
            return html
            
        meta_tags = self._generate_meta_tags(page)
        
        # Insert meta tags after <head>
        if '<head>' in html:
            html = html.replace('<head>', f'<head>\n{meta_tags}')
        else:
            html = meta_tags + html
            
        # Add structured data
        structured_data = self._generate_structured_data(page)
        if structured_data:
            html = html.replace('</body>', f'{structured_data}\n</body>')
            
        return html
        
    def _generate_seo_context(self, page) -> Dict[str, Any]:
        """Generate SEO context for page."""
        title = page.metadata.get('seo_title', page.title)
        description = page.metadata.get(
            'seo_description',
            page.metadata.get('description', self.engine.config.SITE_DESCRIPTION)
        )
        
        return {
            'seo_title': f"{title} - {self.engine.config.SITE_NAME}",
            'seo_description': description,
            'seo_keywords': page.metadata.get('keywords', self.engine.config.SITE_KEYWORDS),
            'seo_author': page.metadata.get('author', self.engine.config.SITE_AUTHOR),
            'seo_image': page.metadata.get('featured_image', '/assets/images/og-image.png'),
            'seo_url': f"{self.engine.config.SITE_URL}{page.url}",
            'seo_type': page.metadata.get('type', 'website'),
        }
        
    def _generate_meta_tags(self, page) -> str:
        """Generate meta tags."""
        tags = []
        seo = self._generate_seo_context(page)
        
        # Basic meta tags
        tags.append(f'<title>{seo["seo_title"]}</title>')
        tags.append(f'<meta name="description" content="{seo["seo_description"]}">')
        
        if seo['seo_keywords']:
            if isinstance(seo['seo_keywords'], list):
                keywords = ', '.join(seo['seo_keywords'])
            else:
                keywords = seo['seo_keywords']
            tags.append(f'<meta name="keywords" content="{keywords}">')
            
        tags.append(f'<meta name="author" content="{seo["seo_author"]}">')
        tags.append(f'<link rel="canonical" href="{seo["seo_url"]}">')
        
        # Open Graph tags
        if self.seo_config.get('generate_og', True):
            og_tags = self._generate_og_tags(seo)
            tags.extend(og_tags)
            
        # Twitter Card tags
        if self.seo_config.get('generate_twitter', True):
            twitter_tags = self._generate_twitter_tags(seo)
            tags.extend(twitter_tags)
            
        # Robots meta
        robots = page.metadata.get('robots', 'index,follow')
        tags.append(f'<meta name="robots" content="{robots}">')
        
        return '\n    '.join(tags)
        
    def _generate_og_tags(self, seo: Dict) -> List[str]:
        """Generate Open Graph tags."""
        og_config = self.seo_config.get('open_graph', {})
        
        return [
            f'<meta property="og:title" content="{seo["seo_title"]}">',
            f'<meta property="og:description" content="{seo["seo_description"]}">',
            f'<meta property="og:type" content="{seo["seo_type"]}">',
            f'<meta property="og:url" content="{seo["seo_url"]}">',
            f'<meta property="og:image" content="{seo["seo_image"]}">',
            f'<meta property="og:site_name" content="{self.engine.config.SITE_NAME}">',
            f'<meta property="og:locale" content="{self.engine.config.SITE_LANG}">',
        ]
        
    def _generate_twitter_tags(self, seo: Dict) -> List[str]:
        """Generate Twitter Card tags."""
        twitter_config = self.seo_config.get('twitter', {})
        
        return [
            f'<meta name="twitter:card" content="{twitter_config.get("card", "summary_large_image")}">',
            f'<meta name="twitter:title" content="{seo["seo_title"]}">',
            f'<meta name="twitter:description" content="{seo["seo_description"]}">',
            f'<meta name="twitter:image" content="{seo["seo_image"]}">',
        ]
        
    def _generate_structured_data(self, page) -> str:
        """Generate structured data (JSON-LD)."""
        seo = self._generate_seo_context(page)
        
        if page.metadata.get('type') == 'post':
            structured_data = {
                '@context': 'https://schema.org',
                '@type': 'BlogPosting',
                'headline': page.title,
                'description': seo['seo_description'],
                'author': {
                    '@type': 'Person',
                    'name': seo['seo_author'],
                },
                'datePublished': page.metadata.get('date', ''),
                'url': seo['seo_url'],
            }
        else:
            structured_data = {
                '@context': 'https://schema.org',
                '@type': 'WebPage',
                'name': page.title,
                'description': seo['seo_description'],
                'url': seo['seo_url'],
            }
            
        return f'<script type="application/ld+json">{json.dumps(structured_data)}</script>'
        
    def register_filters(self, env):
        """Register SEO filters."""
        env.filters['seo_title'] = lambda title: f"{title} - {self.engine.config.SITE_NAME}"
        env.filters['seo_description'] = lambda desc: desc or self.engine.config.SITE_DESCRIPTION
        env.filters['seo_keywords'] = lambda kw: ', '.join(kw) if isinstance(kw, list) else kw
        
    def register_globals(self, env):
        """Register SEO globals."""
        env.globals['seo_config'] = self.seo_config