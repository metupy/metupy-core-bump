# metupy/plugins/sitemap.py
"""Sitemap Plugin - Generate sitemap.xml."""

from metupy.core.plugin_manager import MetupyPlugin
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

class SitemapPlugin(MetupyPlugin):
    """Sitemap generation plugin."""
    
    name = "sitemap"
    version = "1.0.0"
    description = "Generate sitemap.xml for search engines"
    author = "Metupy Team"
    url = "https://metupy.dev/plugins/sitemap"
    
    def __init__(self, engine):
        super().__init__(engine)
        self.sitemap_config = {}
        
    def setup(self):
        """Setup sitemap plugin."""
        self.sitemap_config = self.engine.config.SEO.get('generate_sitemap', True)
        print(f"Sitemap Plugin v{self.version} initialized")
        
    def on_build_end(self, engine):
        """Generate sitemap after build."""
        if not self.sitemap_config:
            return
            
        self._generate_sitemap()
        self._generate_robots()
        
    def _generate_sitemap(self):
        """Generate sitemap.xml."""
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        for page in self.engine.content_manager.pages:
            if page.metadata.get('noindex', False):
                continue
                
            url = ET.SubElement(urlset, 'url')
            
            loc = ET.SubElement(url, 'loc')
            loc.text = f"{self.engine.config.SITE_URL}{page.url}"
            
            # Last modified
            if page.metadata.get('date'):
                lastmod = ET.SubElement(url, 'lastmod')
                lastmod.text = page.metadata['date']
                
            # Change frequency
            changefreq = ET.SubElement(url, 'changefreq')
            changefreq.text = page.metadata.get('changefreq', 'monthly')
            
            # Priority
            priority = ET.SubElement(url, 'priority')
            priority.text = str(page.metadata.get('priority', '0.5'))
            
        # Write sitemap
        tree = ET.ElementTree(urlset)
        sitemap_path = self.engine.output_dir / 'sitemap.xml'
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
        
        print(f"Sitemap generated: {sitemap_path}")
        
    def _generate_robots(self):
        """Generate robots.txt."""
        robots_content = f"""User-agent: *
Allow: /

Sitemap: {self.engine.config.SITE_URL}/sitemap.xml
"""
        
        robots_path = self.engine.output_dir / 'robots.txt'
        robots_path.write_text(robots_content)
        
        print(f"Robots.txt generated: {robots_path}")