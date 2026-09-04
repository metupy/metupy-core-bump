"""
Analytics plugin for Metupy.

Adds Google Analytics tracking code to rendered pages.
"""

from typing import Any, Dict

from metupy.core.plugin_manager import MetupyPlugin


class AnalyticsPlugin(MetupyPlugin):
    """Google Analytics integration plugin."""

    name = "analytics"
    version = "1.0.0"
    description = "Add Google Analytics tracking"
    author = "Metupy Team"

    def __init__(self, engine):
        """Initialize analytics plugin."""
        super().__init__(engine)
        self.tracking_id = ""

    def setup(self) -> None:
        """Setup analytics plugin."""
        seo_config = getattr(self.engine.config, 'SEO', {})
        self.tracking_id = seo_config.get('google_analytics', '')
        print(f"  Analytics Plugin v{self.version} loaded")

    def on_page_after_render(self, page, html: str) -> str:
        """
        Add analytics code to rendered page.

        Args:
            page: Page that was rendered.
            html: Rendered HTML.

        Returns:
            HTML with analytics code.
        """
        if not self.tracking_id:
            return html

        analytics_code = self._generate_code()

        if '</body>' in html:
            html = html.replace('</body>', f'{analytics_code}\n</body>')
        else:
            html += analytics_code

        return html

    def _generate_code(self) -> str:
        """
        Generate Google Analytics 4 code.

        Returns:
            Analytics script HTML.
        """
        return f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.tracking_id}"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{self.tracking_id}');
</script>
"""

    def register_globals(self, env) -> None:
        """Register analytics globals."""
        env.globals['analytics_id'] = self.tracking_id