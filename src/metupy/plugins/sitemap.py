"""
Sitemap plugin for Metupy.

Generates sitemap.xml and robots.txt after build.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from metupy.core.plugin_manager import MetupyPlugin


class SitemapPlugin(MetupyPlugin):
    """Sitemap generation plugin."""

    name = "sitemap"
    version = "1.0.0"
    description = "Generate sitemap.xml for search engines"
    author = "Metupy Team"

    def __init__(self, engine):
        """Initialize sitemap plugin."""
        super().__init__(engine)
        self.sitemap_enabled = True

    def setup(self) -> None:
        """Setup sitemap plugin."""
        seo_config = getattr(self.engine.config, 'SEO', {})
        self.sitemap_enabled = seo_config.get('generate_sitemap', True)
        print(f"  Sitemap Plugin v{self.version} loaded")

    def on_build_end(self, engine) -> None:
        """Generate sitemap after build completes."""
        if not self.sitemap_enabled:
            return

        self._generate_sitemap()
        self._generate_robots()

    def _generate_sitemap(self) -> None:
        """Generate sitemap.xml file."""
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        content_manager = getattr(self.engine, 'content_manager', None)
        page_manager = getattr(self.engine, 'page_manager', None)

        all_pages = []

        if content_manager:
            all_pages.extend(content_manager.pages)

        if page_manager:
            all_pages.extend(page_manager.pages)

        for page in all_pages:
            url = ET.SubElement(urlset, 'url')
            loc = ET.SubElement(url, 'loc')
            loc.text = f"{self.engine.site_context['url']}{page.url}"

            changefreq = ET.SubElement(url, 'changefreq')
            changefreq.text = page.metadata.get('changefreq', 'monthly')

            priority = ET.SubElement(url, 'priority')
            priority.text = str(page.metadata.get('priority', '0.5'))

        tree = ET.ElementTree(urlset)
        sitemap_path = self.engine.output_dir / 'sitemap.xml'
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
        print(f"  Sitemap generated: {sitemap_path}")

    def _generate_robots(self) -> None:
        """Generate robots.txt file."""
        seo_config = getattr(self.engine.config, 'SEO', {})
        if not seo_config.get('generate_robots', True):
            return

        robots_content = f"""User-agent: *
Allow: /

Sitemap: {self.engine.site_context['url']}/sitemap.xml
"""
        robots_path = self.engine.output_dir / 'robots.txt'
        robots_path.write_text(robots_content, encoding='utf-8')
        print(f"  Robots.txt generated: {robots_path}")