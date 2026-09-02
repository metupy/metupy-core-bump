# metupy/core/widget_manager.py
"""Widget Manager - Mengelola widget Metupy."""

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod
from jinja2 import Template

class MetupyWidget(ABC):
    """Base class for Metupy widgets."""
    
    # Widget metadata
    name: str = "base-widget"
    version: str = "0.1.0"
    description: str = "Base widget"
    author: str = "Unknown"
    category: str = "general"
    icon: str = "📦"
    
    # Widget template
    template: str = ""
    
    # Widget settings
    settings_schema: Dict[str, Any] = {}
    
    def __init__(self, engine, **kwargs):
        self.engine = engine
        self.config = kwargs
        self.id = f"widget-{self.name}-{id(self)}"
        
    @abstractmethod
    def get_context(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Get widget context."""
        return {
            'widget': self,
            'config': self.config,
        }
        
    def render(self, context: Optional[Dict] = None) -> str:
        """Render widget to HTML."""
        if self.template:
            template = self.engine.template_env.from_string(self.template)
            return template.render(**self.get_context(context))
        return ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert widget to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'category': self.category,
            'icon': self.icon,
            'config': self.config,
        }

class TextWidget(MetupyWidget):
    """Text widget."""
    
    name = "text"
    description = "Simple text widget"
    category = "basic"
    icon = "📝"
    template = """
<div class="widget widget-text" id="{{ widget.id }}">
    <div class="widget-content">
        {{ config.text | safe }}
    </div>
</div>"""
    
    settings_schema = {
        "text": {
            "type": "textarea",
            "label": "Text Content",
            "default": "",
            "required": True,
        },
        "className": {
            "type": "text",
            "label": "CSS Class",
            "default": "",
        }
    }
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        ctx['text'] = self.config.get('text', '')
        return ctx

class HTMLWidget(MetupyWidget):
    """HTML widget."""
    
    name = "html"
    description = "Raw HTML content"
    category = "basic"
    icon = "💻"
    template = """
<div class="widget widget-html" id="{{ widget.id }}">
    {{ config.html | safe }}
</div>"""
    
    settings_schema = {
        "html": {
            "type": "code",
            "label": "HTML Content",
            "default": "",
        }
    }
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        ctx['html'] = self.config.get('html', '')
        return ctx

class ImageWidget(MetupyWidget):
    """Image widget."""
    
    name = "image"
    description = "Image with optional caption"
    category = "media"
    icon = "🖼️"
    template = """
<figure class="widget widget-image" id="{{ widget.id }}">
    <img src="{{ config.src }}" alt="{{ config.alt }}" 
         class="widget-image-img {{ config.className }}">
    {% if config.caption %}
    <figcaption class="widget-image-caption">{{ config.caption }}</figcaption>
    {% endif %}
</figure>"""
    
    settings_schema = {
        "src": {"type": "text", "label": "Image URL", "required": True},
        "alt": {"type": "text", "label": "Alt Text", "default": ""},
        "caption": {"type": "text", "label": "Caption", "default": ""},
        "className": {"type": "text", "label": "CSS Class", "default": ""},
    }
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        ctx['src'] = self.config.get('src', '')
        ctx['alt'] = self.config.get('alt', '')
        ctx['caption'] = self.config.get('caption', '')
        return ctx

class GalleryWidget(MetupyWidget):
    """Image gallery widget."""
    
    name = "gallery"
    description = "Image gallery with lightbox"
    category = "media"
    icon = "🎨"
    template = """
<div class="widget widget-gallery" id="{{ widget.id }}">
    <div class="gallery-grid">
        {% for image in config.images %}
        <div class="gallery-item">
            <img src="{{ image.url }}" alt="{{ image.caption }}" 
                 data-lightbox="gallery-{{ widget.id }}">
            {% if image.caption %}
            <span class="gallery-caption">{{ image.caption }}</span>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>"""
    
    settings_schema = {
        "images": {
            "type": "list",
            "label": "Images",
            "default": [],
            "items": {
                "url": {"type": "text", "label": "URL", "required": True},
                "caption": {"type": "text", "label": "Caption"},
            }
        },
        "columns": {"type": "number", "label": "Columns", "default": 3},
        "gap": {"type": "number", "label": "Gap (px)", "default": 10},
    }
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        ctx['images'] = self.config.get('images', [])
        ctx['columns'] = self.config.get('columns', 3)
        ctx['gap'] = self.config.get('gap', 10)
        return ctx

class VideoWidget(MetupyWidget):
    """Video widget."""
    
    name = "video"
    description = "Embed video from YouTube, Vimeo, etc."
    category = "media"
    icon = "🎥"
    template = """
<div class="widget widget-video" id="{{ widget.id }}">
    <div class="video-wrapper">
        {% if config.type == 'youtube' %}
        <iframe src="https://www.youtube.com/embed/{{ config.video_id }}"
                frameborder="0" allowfullscreen></iframe>
        {% elif config.type == 'vimeo' %}
        <iframe src="https://player.vimeo.com/video/{{ config.video_id }}"
                frameborder="0" allowfullscreen></iframe>
        {% else %}
        <video controls>
            <source src="{{ config.src }}" type="video/mp4">
        </video>
        {% endif %}
    </div>
</div>"""
    
    settings_schema = {
        "type": {
            "type": "select",
            "label": "Video Type",
            "options": ["youtube", "vimeo", "mp4"],
            "default": "youtube",
        },
        "video_id": {"type": "text", "label": "Video ID"},
        "src": {"type": "text", "label": "Video URL"},
        "autoplay": {"type": "boolean", "label": "Autoplay", "default": False},
    }

class RecentPostsWidget(MetupyWidget):
    """Recent posts widget."""
    
    name = "recent-posts"
    description = "Display recent blog posts"
    category = "blog"
    icon = "📰"
    template = """
<div class="widget widget-recent-posts" id="{{ widget.id }}">
    <h3 class="widget-title">{{ config.title }}</h3>
    <ul class="recent-posts-list">
        {% for post in posts %}
        <li class="recent-post-item">
            <a href="{{ post.url }}">{{ post.title }}</a>
            <span class="post-date">{{ post.date }}</span>
        </li>
        {% endfor %}
    </ul>
</div>"""
    
    settings_schema = {
        "title": {"type": "text", "label": "Widget Title", "default": "Recent Posts"},
        "count": {"type": "number", "label": "Number of Posts", "default": 5},
        "show_date": {"type": "boolean", "label": "Show Date", "default": True},
    }
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        count = self.config.get('count', 5)
        posts = self.engine.content_manager.posts[:count]
        ctx['posts'] = [{
            'title': post.title,
            'url': post.url,
            'date': post.metadata.get('date', ''),
        } for post in posts]
        return ctx

class CategoriesWidget(MetupyWidget):
    """Categories widget."""
    
    name = "categories"
    description = "Display post categories"
    category = "blog"
    icon = "🏷️"
    template = """
<div class="widget widget-categories" id="{{ widget.id }}">
    <h3 class="widget-title">{{ config.title }}</h3>
    <ul class="categories-list">
        {% for category in categories %}
        <li class="category-item">
            <a href="/category/{{ category.slug }}/">{{ category.name }}</a>
            <span class="category-count">{{ category.count }}</span>
        </li>
        {% endfor %}
    </ul>
</div>"""
    
    def get_context(self, context=None):
        ctx = super().get_context(context)
        # Get all categories from posts
        categories = {}
        for post in self.engine.content_manager.posts:
            for category in post.metadata.get('categories', []):
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
                
        ctx['categories'] = [
            {'name': name, 'slug': name.lower().replace(' ', '-'), 'count': count}
            for name, count in categories.items()
        ]
        return ctx

class SearchWidget(MetupyWidget):
    """Search widget."""
    
    name = "search"
    description = "Search form"
    category = "utility"
    icon = "🔍"
    template = """
<div class="widget widget-search" id="{{ widget.id }}">
    <form action="{{ config.action }}" method="get" class="search-form">
        <input type="search" name="q" placeholder="{{ config.placeholder }}"
               class="search-input">
        <button type="submit" class="search-button">
            {{ config.button_text }}
        </button>
    </form>
</div>"""
    
    settings_schema = {
        "placeholder": {"type": "text", "label": "Placeholder", "default": "Search..."},
        "button_text": {"type": "text", "label": "Button Text", "default": "Search"},
        "action": {"type": "text", "label": "Form Action", "default": "/search"},
    }

class WidgetManager:
    """Manages Metupy widgets."""
    
    def __init__(self, engine):
        self.engine = engine
        self.widgets: Dict[str, Type[MetupyWidget]] = {}
        self.widget_instances: Dict[str, MetupyWidget] = {}
        self.registered_widgets = []
        
    async def load_widgets(self):
        """Load all widgets."""
        # Load built-in widgets
        self._load_builtin_widgets()
        
        # Load user widgets
        await self._load_user_widgets()
        
    def _load_builtin_widgets(self):
        """Load built-in widgets."""
        builtin_widgets = [
            TextWidget,
            HTMLWidget,
            ImageWidget,
            GalleryWidget,
            VideoWidget,
            RecentPostsWidget,
            CategoriesWidget,
            SearchWidget,
        ]
        
        for widget_class in builtin_widgets:
            self.register_widget(widget_class)
            
    async def _load_user_widgets(self):
        """Load user widgets from widgets directory."""
        widgets_dir = Path(self.engine.config.WIDGETS_DIR)
        
        if not widgets_dir.exists():
            return
            
        for widget_file in widgets_dir.glob('*.py'):
            await self._load_widget_from_file(widget_file)
            
    async def _load_widget_from_file(self, widget_file: Path):
        """Load widget from file."""
        try:
            spec = importlib.util.spec_from_file_location(
                f"metupy_widget_{widget_file.stem}",
                widget_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, MetupyWidget):
                    if obj != MetupyWidget:
                        self.register_widget(obj)
                        
        except Exception as e:
            print(f"Error loading widget {widget_file.name}: {e}")
            
    def register_widget(self, widget_class: Type[MetupyWidget]):
        """Register widget class."""
        self.widgets[widget_class.name] = widget_class
        
        # Add to registered widgets list
        self.registered_widgets.append({
            'name': widget_class.name,
            'version': widget_class.version,
            'description': widget_class.description,
            'author': widget_class.author,
            'category': widget_class.category,
            'icon': widget_class.icon,
            'settings_schema': widget_class.settings_schema,
        })
        
    def create_widget(self, name: str, **kwargs) -> Optional[MetupyWidget]:
        """Create widget instance."""
        if name not in self.widgets:
            return None
            
        widget_class = self.widgets[name]
        instance = widget_class(self.engine, **kwargs)
        self.widget_instances[instance.id] = instance
        return instance
        
    def render_widget(self, name: str, context: Optional[Dict] = None, **kwargs) -> str:
        """Create and render widget."""
        widget = self.create_widget(name, **kwargs)
        if widget:
            return widget.render(context)
        return ""
        
    def get_widget(self, name: str) -> Optional[Type[MetupyWidget]]:
        """Get widget class by name."""
        return self.widgets.get(name)
        
    def list_widgets(self) -> List[Dict[str, Any]]:
        """List all registered widgets."""
        return self.registered_widgets
        
    def get_widgets_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get widgets by category."""
        return [
            w for w in self.registered_widgets
            if w['category'] == category
        ]