"""
Widget manager for Metupy.

Provides widget registration, creation, and rendering.
"""

from typing import Any, Callable, Dict, List, Optional, Type


class MetupyWidget:
    """Base class for all Metupy widgets."""

    name: str = "base-widget"
    version: str = "1.0.0"
    description: str = "Base widget"
    author: str = "Unknown"
    category: str = "general"
    icon: str = "📦"
    template: str = ""

    def __init__(self, engine, **kwargs):
        """
        Initialize widget.

        Args:
            engine: MetupyEngine instance.
            **kwargs: Widget configuration.
        """
        self.engine = engine
        self.config = kwargs
        self.id = f"widget-{self.name}-{id(self)}"

    def get_context(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get widget rendering context.

        Args:
            context: Optional additional context.

        Returns:
            Context dictionary.
        """
        ctx = {
            'widget': self,
            'config': self.config,
            'engine': self.engine,
        }
        if context:
            ctx.update(context)
        return ctx

    def render(self, context: Optional[Dict] = None) -> str:
        """
        Render widget to HTML.

        Args:
            context: Optional rendering context.

        Returns:
            Rendered HTML string.
        """
        if not self.template:
            return ""

        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return ""

        template = template_env.from_string(self.template)
        return template.render(**self.get_context(context))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert widget to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'config': self.config,
        }


class TextWidget(MetupyWidget):
    """Simple text widget."""

    name = "text"
    description = "Simple text widget"
    category = "basic"
    icon = "📝"
    template = """
<div class="widget widget-text">
    <div class="widget-content">{{ config.text | safe }}</div>
</div>"""

    def get_context(self, context=None):
        """Get widget context."""
        ctx = super().get_context(context)
        ctx['text'] = self.config.get('text', '')
        return ctx


class HTMLWidget(MetupyWidget):
    """Raw HTML widget."""

    name = "html"
    description = "Raw HTML content"
    category = "basic"
    icon = "💻"
    template = """
<div class="widget widget-html">{{ config.html | safe }}</div>"""


class RecentPostsWidget(MetupyWidget):
    """Recent posts widget."""

    name = "recent-posts"
    description = "Display recent blog posts"
    category = "blog"
    icon = "📰"
    template = """
<div class="widget widget-recent-posts">
    <h3>{{ config.title | default('Recent Posts') }}</h3>
    <ul>
        {% for post in posts %}
        <li><a href="{{ post.url }}">{{ post.title }}</a></li>
        {% endfor %}
    </ul>
</div>"""

    def get_context(self, context=None):
        """Get widget context with recent posts."""
        ctx = super().get_context(context)
        count = self.config.get('count', 5)

        posts = []
        content_manager = getattr(self.engine, 'content_manager', None)
        if content_manager:
            posts = [
                {'title': p.title, 'url': p.url}
                for p in content_manager.posts[:count]
            ]

        ctx['posts'] = posts
        return ctx


class SearchWidget(MetupyWidget):
    """Search form widget."""

    name = "search"
    description = "Search form"
    category = "utility"
    icon = "🔍"
    template = """
<div class="widget widget-search">
    <form action="/search" method="get">
        <input type="search" name="q" placeholder="{{ config.placeholder | default('Search...') }}">
        <button type="submit">Search</button>
    </form>
</div>"""


class WidgetManager:
    """Manage Metupy widgets."""

    def __init__(self, engine):
        """
        Initialize WidgetManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.widgets: Dict[str, Type[MetupyWidget]] = {}
        self.widget_instances: Dict[str, MetupyWidget] = {}
        self.registered_widgets: List[Dict] = []

    async def load_widgets(self) -> None:
        """Load all widgets."""
        self._load_builtin_widgets()

    def _load_builtin_widgets(self) -> None:
        """Load built-in widgets."""
        builtin = [
            TextWidget,
            HTMLWidget,
            RecentPostsWidget,
            SearchWidget,
        ]

        for widget_class in builtin:
            self.register_widget(widget_class)

    def register_widget(self, widget_class: Type[MetupyWidget]) -> None:
        """
        Register widget class.

        Args:
            widget_class: Widget class to register.
        """
        self.widgets[widget_class.name] = widget_class

        self.registered_widgets.append({
            'name': widget_class.name,
            'version': widget_class.version,
            'description': widget_class.description,
            'category': widget_class.category,
            'icon': widget_class.icon,
        })

    def create_widget(self, name: str, **kwargs) -> Optional[MetupyWidget]:
        """
        Create widget instance.

        Args:
            name: Widget name.
            **kwargs: Widget configuration.

        Returns:
            Widget instance or None.
        """
        widget_class = self.widgets.get(name)
        if not widget_class:
            return None

        instance = widget_class(self.engine, **kwargs)
        self.widget_instances[instance.id] = instance
        return instance

    def render_widget(self, name: str, context: Optional[Dict] = None, **kwargs) -> str:
        """
        Create and render widget.

        Args:
            name: Widget name.
            context: Optional rendering context.
            **kwargs: Widget configuration.

        Returns:
            Rendered HTML string.
        """
        widget = self.create_widget(name, **kwargs)
        if widget:
            return widget.render(context)
        return ""

    def get_widget(self, name: str) -> Optional[Type[MetupyWidget]]:
        """
        Get widget class by name.

        Args:
            name: Widget name.

        Returns:
            Widget class or None.
        """
        return self.widgets.get(name)

    def list_widgets(self) -> List[Dict]:
        """
        List all registered widgets.

        Returns:
            List of widget metadata dictionaries.
        """
        return self.registered_widgets

    def get_widgets_by_category(self, category: str) -> List[Dict]:
        """
        Get widgets by category.

        Args:
            category: Category name.

        Returns:
            List of widget metadata.
        """
        return [w for w in self.registered_widgets if w['category'] == category]