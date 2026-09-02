# metupy/plugins/rss.py
"""RSS Plugin - Generate RSS feed."""

from metupy.core.plugin_manager import MetupyPlugin
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

class RSSPlugin(MetupyPlugin):
    """RSS feed generation plugin."""
    
    name = "rss"
    version = "1.0.0"
    description = "Generate RSS feed for blog posts"
    author = "Metupy Team"
    url = "https://metupy.dev/plugins/rss"
    
    def __init__(self, engine):
        super().__init__(engine)
        self.rss_config = {}
        
    def setup(self):
        """Setup RSS plugin."""
        self.rss_config = self.engine.config.BUILD_GENERATE_FEED
        print(f"RSS Plugin v{self.version} initialized")
        
    def on_build_end(self, engine):
        """Generate RSS feed after build."""
        if not self.rss_config:
            return
            
        self._generate_rss()
        self._generate_atom()
        
    def _generate_rss(self):
        """Generate RSS 2.0 feed."""
        rss = ET.Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
        
        channel = ET.SubElement(rss, 'channel')
        
        # Channel metadata
        title = ET.SubElement(channel, 'title')
        title.text = self.engine.config.SITE_NAME
        
        link = ET.SubElement(channel, 'link')
        link.text = self.engine.config.SITE_URL
        
        description = ET.SubElement(channel, 'description')
        description.text = self.engine.config.SITE_DESCRIPTION
        
        language = ET.SubElement(channel, 'language')
        language.text = self.engine.config.SITE_LANG
        
        last_build = ET.SubElement(channel, 'lastBuildDate')
        last_build.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Add posts
        for post in self.engine.content_manager.posts[:20]:  # Last 20 posts
            item = ET.SubElement(channel, 'item')
            
            item_title = ET.SubElement(item, 'title')
            item_title.text = post.title
            
            item_link = ET.SubElement(item, 'link')
            item_link.text = f"{self.engine.config.SITE_URL}{post.url}"
            
            item_desc = ET.SubElement(item, 'description')
            item_desc.text = post.metadata.get('description', '')
            
            if post.metadata.get('date'):
                pub_date = ET.SubElement(item, 'pubDate')
                pub_date.text = post.metadata['date']
                
            if post.metadata.get('author'):
                author = ET.SubElement(item, 'author')
                author.text = post.metadata['author']
                
            # Categories
            for tag in post.metadata.get('tags', []):
                category = ET.SubElement(item, 'category')
                category.text = tag
                
        # Write RSS
        tree = ET.ElementTree(rss)
        rss_path = self.engine.output_dir / 'feed.xml'
        tree.write(rss_path, encoding='utf-8', xml_declaration=True)
        
        print(f"RSS feed generated: {rss_path}")
        
    def _generate_atom(self):
        """Generate Atom feed."""
        atom = ET.Element('feed')
        atom.set('xmlns', 'http://www.w3.org/2005/Atom')
        
        # Feed metadata
        title = ET.SubElement(atom, 'title')
        title.text = self.engine.config.SITE_NAME
        
        link = ET.SubElement(atom, 'link')
        link.set('href', self.engine.config.SITE_URL)
        
        updated = ET.SubElement(atom, 'updated')
        updated.text = datetime.now().isoformat()
        
        author = ET.SubElement(atom, 'author')
        name = ET.SubElement(author, 'name')
        name.text = self.engine.config.SITE_AUTHOR
        
        feed_id = ET.SubElement(atom, 'id')
        feed_id.text = self.engine.config.SITE_URL
        
        # Add entries
        for post in self.engine.content_manager.posts[:20]:
            entry = ET.SubElement(atom, 'entry')
            
            entry_title = ET.SubElement(entry, 'title')
            entry_title.text = post.title
            
            entry_link = ET.SubElement(entry, 'link')
            entry_link.set('href', f"{self.engine.config.SITE_URL}{post.url}")
            
            entry_id = ET.SubElement(entry, 'id')
            entry_id.text = f"{self.engine.config.SITE_URL}{post.url}"
            
            entry_updated = ET.SubElement(entry, 'updated')
            entry_updated.text = post.metadata.get('date', datetime.now().isoformat())
            
            entry_summary = ET.SubElement(entry, 'summary')
            entry_summary.text = post.metadata.get('description', '')
            
        # Write Atom
        tree = ET.ElementTree(atom)
        atom_path = self.engine.output_dir / 'atom.xml'
        tree.write(atom_path, encoding='utf-8', xml_declaration=True)
        
        print(f"Atom feed generated: {atom_path}")