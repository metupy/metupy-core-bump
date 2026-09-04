"""
RSS plugin for Metupy.

Generates RSS 2.0 feed for blog posts.
"""

import xml.etree.ElementTree as ET
from datetime import datetime

from metupy.core.plugin_manager import MetupyPlugin


class RSSPlugin(MetupyPlugin):
    """RSS feed generation plugin."""

    name = "rss"
    version = "1.0.0"
    description = "Generate RSS feed for blog posts"
    author = "Metupy Team"

    def __init__(self, engine):
        """Initialize RSS plugin."""
        super().__init__(engine)
        self.rss_enabled = True

    def setup(self) -> None:
        """Setup RSS plugin."""
        self.rss_enabled = getattr(self.engine.config, 'BUILD_GENERATE_FEED', True)
        print(f"  RSS Plugin v{self.version} loaded")

    def on_build_end(self, engine) -> None:
        """Generate RSS feed after build."""
        if not self.rss_enabled:
            return

        self._generate_rss()

    def _generate_rss(self) -> None:
        """Generate RSS 2.0 feed."""
        rss = ET.Element('rss')
        rss.set('version', '2.0')

        channel = ET.SubElement(rss, 'channel')

        title = ET.SubElement(channel, 'title')
        title.text = self.engine.site_context['name']

        link = ET.SubElement(channel, 'link')
        link.text = self.engine.site_context['url']

        description = ET.SubElement(channel, 'description')
        description.text = getattr(self.engine.config, 'SITE_DESCRIPTION', '')

        language = ET.SubElement(channel, 'language')
        language.text = getattr(self.engine.config, 'SITE_LANG', 'en')

        last_build = ET.SubElement(channel, 'lastBuildDate')
        last_build.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')

        content_manager = getattr(self.engine, 'content_manager', None)
        if content_manager:
            for post in content_manager.posts[:20]:
                item = ET.SubElement(channel, 'item')

                item_title = ET.SubElement(item, 'title')
                item_title.text = post.title

                item_link = ET.SubElement(item, 'link')
                item_link.text = f"{self.engine.site_context['url']}{post.url}"

                item_desc = ET.SubElement(item, 'description')
                item_desc.text = post.metadata.get('description', '')

                if post.metadata.get('date'):
                    pub_date = ET.SubElement(item, 'pubDate')
                    pub_date.text = post.metadata['date']

        tree = ET.ElementTree(rss)
        rss_path = self.engine.output_dir / 'feed.xml'
        tree.write(rss_path, encoding='utf-8', xml_declaration=True)
        print(f"  RSS feed generated: {rss_path}")