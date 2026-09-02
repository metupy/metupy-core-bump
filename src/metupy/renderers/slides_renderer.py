# metupy/renderers/slides_renderer.py
"""Slides Renderer."""

from typing import Dict, Any, List
from pathlib import Path

class SlidesRenderer:
    """Renders slide presentations."""
    
    def __init__(self, engine):
        self.engine = engine
        
    async def render_slides(self, page) -> str:
        """Render slides."""
        # Split content into slides
        slides = self._split_slides(page.content)
        
        context = {
            'slides': slides,
            'total_slides': len(slides),
            'presentation_title': page.title,
            'theme': page.metadata.get('theme', 'default'),
            'transition': page.metadata.get('transition', 'slide'),
        }
        
        template = self.engine.template_env.get_template('slides.html')
        return template.render(**context)
        
    def _split_slides(self, content: str) -> List[Dict]:
        """Split content into slides."""
        slides = []
        
        # Split by horizontal rule or slide separator
        parts = content.split('---')
        
        for i, part in enumerate(parts):
            slide = {
                'number': i + 1,
                'content': part.strip(),
                'background': None,
                'notes': None,
            }
            
            # Extract slide metadata
            if '???' in part:
                slide_content, notes = part.split('???', 1)
                slide['content'] = slide_content.strip()
                slide['notes'] = notes.strip()
                
            slides.append(slide)
            
        return slides