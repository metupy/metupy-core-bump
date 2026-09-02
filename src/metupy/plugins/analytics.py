# metupy/plugins/analytics.py
"""Analytics Plugin - Add analytics tracking."""

from metupy.core.plugin_manager import MetupyPlugin
from typing import Dict, Any
import json

class AnalyticsPlugin(MetupyPlugin):
    """Analytics tracking plugin."""
    
    name = "analytics"
    version = "1.0.0"
    description = "Add analytics tracking to your site"
    author = "Metupy Team"
    url = "https://metupy.dev/plugins/analytics"
    
    def __init__(self, engine):
        super().__init__(engine)
        self.analytics_config = {}
        
    def setup(self):
        """Setup analytics plugin."""
        self.analytics_config = self.engine.config.SEO.get('google_analytics', '')
        print(f"Analytics Plugin v{self.version} initialized")
        
    def on_page_after_render(self, page, html):
        """Add analytics code to page."""
        if not self.analytics_config:
            return html
            
        analytics_code = self._generate_analytics_code()
        
        # Insert before </body>
        if '</body>' in html:
            html = html.replace('</body>', f'{analytics_code}\n</body>')
        else:
            html += analytics_code
            
        return html
        
    def _generate_analytics_code(self) -> str:
        """Generate analytics code."""
        # Google Analytics 4
        ga_code = f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.analytics_config}"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{self.analytics_config}');
</script>
"""
        
        return ga_code
        
    def register_globals(self, env):
        """Register analytics globals."""
        env.globals['analytics_id'] = self.analytics_config