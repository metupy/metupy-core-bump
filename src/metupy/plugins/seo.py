"""
SEO plugin for Metupy.

Adds SEO meta tags, Open Graph tags, and Twitter Cards
to rendered pages.
"""

from typing import Any, Dict, List

from metupy.core.plugin_manager import MetupyPlugin


class SEOPlugin(MetupyPlugin):
    """SEO optimization plugin."""

    name = "seo"
    version = "1.0.0"
    description = "SEO optimization for Metupy sites"
    author = "Metupy Team"

    def __init__(self, engine):
        """Initialize SEO plugin."""
        super().__init__(engine)
        self.seo_config = {}

    def setup(self) -> None:
        """Setup SEO plugin."""
        self.seo_config = getattr(self.engine.config, 'SEO', {})
        print(f"  SEO Plugin v{self.version} loaded")

    def on_page_after_render(self, page, html: str) -> str:
        """
        Add SEO meta tags to rendered page.

        Args:
            page: Page that was rendered.
            html: Rendered HTML.

        Returns:
            HTML with SEO meta tags.
        """
        if not self.seo_config.get('generate_meta', True):
            return html

        meta_tags = self._generate_meta_tags(page)

        if '<head>' in html:
            html = html.replace('<head>', f'<head>\n{meta_tags}')
        else:
            html = meta_tags + html

        return html

    def _generate_meta_tags(self, page) -> str:
        """
        Generate SEO meta tags for page.

        Args:
            page: Page to generate tags for.

        Returns:
            Meta tags HTML string.
        """
        tags = []

        title = page.metadata.get('seo_title', page.title)
        description = page.metadata.get('description', getattr(self.engine.config, 'SITE_DESCRIPTION', ''))

        tags.append(f'<title>{title} - {self.engine.site_context["name"]}</title>')
        tags.append(f'<meta name="description" content="{description}">')

        keywords = page.metadata.get('keywords', getattr(self.engine.config, 'SITE_KEYWORDS', []))
        if keywords:
            if isinstance(keywords, list):
                keywords = ', '.join(keywords)
            tags.append(f'<meta name="keywords" content="{keywords}">')

        tags.append(f'<meta name="author" content="{getattr(self.engine.config, "SITE_AUTHOR", "")}">')
        tags.append(f'<link rel="canonical" href="{self.engine.site_context["url"]}{page.url}">')

        if self.seo_config.get('generate_og', True):
            tags.extend(self._generate_og_tags(page, title, description))

        if self.seo_config.get('generate_twitter', True):
            tags.extend(self._generate_twitter_tags(page, title, description))

        return '\n    '.join(tags)

    def _generate_og_tags(self, page, title: str, description: str) -> List[str]:
        """
        Generate Open Graph tags.

        Args:
            page: Page instance.
            title: Page title.
            description: Page description.

        Returns:
            List of OG meta tags.
        """
        return [
            f'<meta property="og:title" content="{title}">',
            f'<meta property="og:description" content="{description}">',
            f'<meta property="og:type" content="website">',
            f'<meta property="og:url" content="{self.engine.site_context["url"]}{page.url}">',
            f'<meta property="og:site_name" content="{self.engine.site_context["name"]}">',
        ]

    def _generate_twitter_tags(self, page, title: str, description: str) -> List[str]:
        """
        Generate Twitter Card tags.

        Args:
            page: Page instance.
            title: Page title.
            description: Page description.

        Returns:
            List of Twitter meta tags.
        """
        return [
            f'<meta name="twitter:card" content="summary">',
            f'<meta name="twitter:title" content="{title}">',
            f'<meta name="twitter:description" content="{description}">',
        ]

    def register_filters(self, env) -> None:
        """Register SEO Jinja2 filters."""
        env.filters['seo_title'] = lambda title: f"{title} - {self.engine.site_context['name']}"
        env.filters['seo_description'] = lambda desc: desc or getattr(self.engine.config, 'SITE_DESCRIPTION', '')