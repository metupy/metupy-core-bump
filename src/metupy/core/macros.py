"""
Macro system for Metupy.

Provides safe macro evaluation using Jinja2 templates.
Macros are registered functions callable from .pym files.
"""

import re
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from jinja2 import Template, TemplateSyntaxError


class MacroManager:
    """Manage macros for .pym file processing."""

    def __init__(self, engine):
        """
        Initialize MacroManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.macros: Dict[str, str] = {}
        self.functions: Dict[str, Callable] = {}
        self._load_builtin_macros()
        self._load_builtin_functions()
        self._load_custom_macros()

    def _load_builtin_macros(self) -> None:
        """Register built-in macros as Jinja2 templates."""
        self.register_macro('date', "{{ now.strftime('%Y-%m-%d') }}")
        self.register_macro('datetime', "{{ now.strftime('%Y-%m-%d %H:%M:%S') }}")
        self.register_macro('time', "{{ now.strftime('%H:%M:%S') }}")
        self.register_macro('year', "{{ now.year }}")
        self.register_macro('month', "{{ now.month }}")
        self.register_macro('day', "{{ now.day }}")
        self.register_macro('site_name', "{{ site.name }}")
        self.register_macro('site_url', "{{ site.url }}")
        self.register_macro('site_description', "{{ site.description }}")
        self.register_macro('site_author', "{{ site.author }}")

    def _load_builtin_functions(self) -> None:
        """Register built-in safe functions."""
        self.register_function('upper', str.upper)
        self.register_function('lower', str.lower)
        self.register_function('strip', str.strip)
        self.register_function('len', len)
        self.register_function('slugify', self._slugify)
        self.register_function('truncate', self._truncate)
        self.register_function('word_count', self._word_count)
        self.register_function('read_time', self._read_time)
        self.register_function('current_year', lambda: datetime.now().year)
        self.register_function('current_month', lambda: datetime.now().month)
        self.register_function('current_day', lambda: datetime.now().day)

    def _load_custom_macros(self) -> None:
        """Load custom macros from pymconfig.py."""
        custom_macros = getattr(self.engine.config, 'CUSTOM_MACROS', {})
        for name, template in custom_macros.items():
            if isinstance(template, str):
                self.register_macro(name, template)

        custom_functions = getattr(self.engine.config, 'CUSTOM_FUNCTIONS', {})
        for name, func in custom_functions.items():
            if callable(func):
                self.register_function(name, func)

    def register_macro(self, name: str, template: str) -> None:
        """
        Register a macro template.

        Args:
            name: Macro name.
            template: Jinja2 template string.
        """
        self.macros[name] = template

    def register_function(self, name: str, func: Callable) -> None:
        """
        Register a safe function.

        Args:
            name: Function name.
            func: Callable function.
        """
        self.functions[name] = func

    def unregister(self, name: str) -> None:
        """
        Unregister macro or function.

        Args:
            name: Name to unregister.
        """
        self.macros.pop(name, None)
        self.functions.pop(name, None)

    def render_macro(self, name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a macro with context.

        Args:
            name: Macro name.
            context: Optional context variables.

        Returns:
            Rendered macro output.
        """
        template_str = self.macros.get(name)
        if not template_str:
            return f"[Macro '{name}' not found]"

        try:
            template = Template(template_str)
            safe_context = self._build_context(context)
            return template.render(**safe_context)
        except TemplateSyntaxError as e:
            return f"[Macro syntax error: {e}]"
        except Exception as e:
            return f"[Macro error: {e}]"

    def call_function(self, name: str, *args, **kwargs) -> Any:
        """
        Call a registered function.

        Args:
            name: Function name.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Function result or error string.
        """
        func = self.functions.get(name)
        if not func:
            return f"[Function '{name}' not found]"

        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f"[Function error: {e}]"

    def _build_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build safe context for macro rendering.

        Args:
            extra: Additional context variables.

        Returns:
            Complete context dictionary.
        """
        context = {
            'now': datetime.now(),
            'site': getattr(self.engine, 'site_context', {}),
            'config': getattr(self.engine.config, 'get_all', lambda: {})(),
            'functions': self.functions,
        }

        if extra:
            context.update(extra)

        return context

    def _slugify(self, text: str) -> str:
        """
        Convert text to URL-safe slug.

        Args:
            text: Input text.

        Returns:
            Slugified string.
        """
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        return text.strip('-')

    def _truncate(self, text: str, length: int = 100) -> str:
        """
        Truncate text to specified length.

        Args:
            text: Input text.
            length: Maximum length.

        Returns:
            Truncated text.
        """
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '...'

    def _word_count(self, text: str) -> int:
        """
        Count words in text.

        Args:
            text: Input text.

        Returns:
            Word count.
        """
        return len(text.split())

    def _read_time(self, text: str) -> str:
        """
        Calculate estimated reading time.

        Args:
            text: Content text.

        Returns:
            Reading time string.
        """
        words = len(text.split())
        minutes = max(1, round(words / 200))
        return f"{minutes} min read"

    def list_macros(self) -> Dict[str, str]:
        """
        List all registered macros.

        Returns:
            Dictionary of macro names to templates.
        """
        return self.macros.copy()

    def list_functions(self) -> List[str]:
        """
        List all registered function names.

        Returns:
            List of function names.
        """
        return list(self.functions.keys())