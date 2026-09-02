"""Custom Plugin Example."""

from metupy.core.plugin_manager import MetupyPlugin
from typing import Dict, Any

class CustomPlugin(MetupyPlugin):
    """Custom plugin example."""
    
    name = "custom-plugin"
    version = "1.0.0"
    description = "Custom plugin for Metupy"
    author = "Your Name"
    dependencies = ["seo"]  # Depends on SEO plugin
    
    def setup(self):
        """Setup plugin."""
        print(f"Setting up {self.name} v{self.version}")
        
    def on_build_start(self, engine):
        """Called when build starts."""
        print("Custom plugin: Build started")
        
    def on_build_end(self, engine):
        """Called when build ends."""
        print("Custom plugin: Build completed")
        
    def on_page_after_render(self, page, html):
        """Add custom content to rendered page."""
        # Add custom footer
        custom_footer = """
        <footer class="custom-footer">
            <p>Powered by Custom Plugin</p>
        </footer>
        """
        return html.replace('</body>', f'{custom_footer}</body>')
        
    def register_filters(self, env):
        """Register custom filters."""
        env.filters['custom_filter'] = lambda text: text.upper()
        
    def register_globals(self, env):
        """Register custom globals."""
        env.globals['custom_global'] = "Custom Global Value"
        