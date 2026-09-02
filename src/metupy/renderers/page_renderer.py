# metupy/renderers/page_renderer.py
"""Page Renderer."""

from typing import Dict, Any, Optional
from pathlib import Path

class PageRenderer:
    """Renders pages."""
    
    def __init__(self, engine):
        self.engine = engine
        
    async def render(self, page, context: Optional[Dict] = None) -> str:
        """Render page."""
        render_context = page.get_context()
        if context:
            render_context.update(context)
            
        # Execute before render hooks
        render_context = await self.engine.plugin_manager.execute_hook(
            'on_page_before_render',
            page=page,
            context=render_context
        )
        
        # Render template
        template = self.engine.template_env.get_template(page.template)
        html = template.render(**render_context)
        
        # Execute after render hooks
        html = await self.engine.plugin_manager.execute_hook(
            'on_page_after_render',
            page=page,
            html=html
        )
        
        return html