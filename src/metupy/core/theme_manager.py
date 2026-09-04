"""
Theme manager for Metupy.

Handles loading, registration, and management of themes.
Supports modular themes with partials directory.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class Theme:
    """Represents a Metupy theme."""

    def __init__(self, name: str, path: Path):
        """
        Initialize Theme instance.

        Args:
            name: Theme name.
            path: Path to theme directory.
        """
        self.name = name
        self.path = path
        self.config: Dict[str, Any] = {}
        self.templates: Dict[str, Path] = {}
        self.partials: Dict[str, Path] = {}
        self.static_files: Dict[str, Path] = {}
        self.css_files: Dict[str, Path] = {}
        self.js_files: Dict[str, Path] = {}

    def load(self) -> None:
        """Load theme configuration and file mappings."""
        theme_file = self.path / 'theme.json'
        if theme_file.exists():
            try:
                self.config = json.loads(theme_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.config = {}

        templates_dir = self.path / 'templates'
        if templates_dir.exists():
            for template in templates_dir.rglob('*.html'):
                relative = template.relative_to(templates_dir)
                relative_str = str(relative).replace('\\', '/')

                if relative_str.startswith('_partials/') or relative_str.startswith('_'):
                    self.partials[relative_str] = template
                else:
                    self.templates[relative_str] = template

        static_dir = self.path / 'static'
        if static_dir.exists():
            for static_file in static_dir.rglob('*'):
                if static_file.is_file():
                    relative = static_file.relative_to(static_dir)
                    relative_str = str(relative).replace('\\', '/')
                    self.static_files[relative_str] = static_file

                    if static_file.suffix == '.css':
                        self.css_files[relative_str] = static_file
                    elif static_file.suffix == '.js':
                        self.js_files[relative_str] = static_file

    def get_settings(self) -> Dict[str, Any]:
        """
        Get theme settings.

        Returns:
            Theme configuration dictionary.
        """
        return self.config

    def get_template(self, name: str) -> Optional[Path]:
        """
        Get template file path.

        Args:
            name: Template name.

        Returns:
            Path to template or None.
        """
        return self.templates.get(name)

    def get_partial(self, name: str) -> Optional[Path]:
        """
        Get partial template file path.

        Args:
            name: Partial template name (e.g., '_partials/_header.html' or '_header.html').

        Returns:
            Path to partial or None.
        """
        if name in self.partials:
            return self.partials[name]

        for partial_name, partial_path in self.partials.items():
            if partial_name.endswith(name):
                return partial_path
            if partial_name.endswith(f'/{name}') or partial_name.endswith(f'\\{name}'):
                return partial_path

        return None

    def get_static_file(self, name: str) -> Optional[Path]:
        """
        Get static file path.

        Args:
            name: Static file name.

        Returns:
            Path to static file or None.
        """
        return self.static_files.get(name)

    def get_css_file(self, name: str) -> Optional[Path]:
        """
        Get CSS file path.

        Args:
            name: CSS file name.

        Returns:
            Path to CSS file or None.
        """
        return self.css_files.get(name)

    def get_js_file(self, name: str) -> Optional[Path]:
        """
        Get JS file path.

        Args:
            name: JS file name.

        Returns:
            Path to JS file or None.
        """
        return self.js_files.get(name)

    def list_templates(self) -> List[str]:
        """
        List all template names.

        Returns:
            List of template names.
        """
        return list(self.templates.keys())

    def list_partials(self) -> List[str]:
        """
        List all partial names.

        Returns:
            List of partial names.
        """
        return list(self.partials.keys())

    def list_css_files(self) -> List[str]:
        """
        List all CSS files.

        Returns:
            List of CSS file names.
        """
        return list(self.css_files.keys())

    def list_js_files(self) -> List[str]:
        """
        List all JS files.

        Returns:
            List of JS file names.
        """
        return list(self.js_files.keys())

    def __repr__(self) -> str:
        """String representation of Theme."""
        return f"<Theme {self.name}>"


class ThemeManager:
    """Manage themes for Metupy engine."""

    def __init__(self, engine):
        """
        Initialize ThemeManager.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.themes: Dict[str, Theme] = {}
        self.active_theme: Optional[Theme] = None

    async def load_theme(self) -> None:
        """Load active theme from configuration."""
        theme_name = getattr(self.engine.config, 'ACTIVE_THEME', 'peradocs')
        theme_path = self.engine.theme_dir

        if theme_path.exists():
            theme = Theme(theme_name, theme_path)
            theme.load()
            self.themes[theme_name] = theme
            self.active_theme = theme
            print(f"  Theme loaded: {theme_name}")
            print(f"    Templates: {len(theme.templates)}")
            print(f"    Partials: {len(theme.partials)}")
            print(f"    CSS: {len(theme.css_files)}")
            print(f"    JS: {len(theme.js_files)}")
        else:
            print(f"  Theme directory not found: {theme_path}")
            self._create_default_theme(theme_name, theme_path)

    def _create_default_theme(self, theme_name: str, theme_path: Path) -> None:
        """
        Create default theme directory with basic structure.

        Args:
            theme_name: Theme name.
            theme_path: Path to create theme at.
        """
        theme_path.mkdir(parents=True, exist_ok=True)
        (theme_path / 'templates').mkdir(exist_ok=True)
        (theme_path / 'templates' / '_partials').mkdir(exist_ok=True)
        (theme_path / 'static').mkdir(exist_ok=True)
        (theme_path / 'static' / 'css').mkdir(exist_ok=True)
        (theme_path / 'static' / 'js').mkdir(exist_ok=True)

        theme_config = {
            "name": theme_name,
            "version": "1.0.0",
            "description": "Default Theme",
            "author": "Metupy Team",
        }
        (theme_path / 'theme.json').write_text(
            json.dumps(theme_config, indent=2),
            encoding='utf-8'
        )

        base_template = '''<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site.name }}</title>
    <link rel="icon" type="image/png" href="/favicon.png">
</head>
<body>
    <header>
        <nav>
            <a href="/">{{ site.name }}</a>
            <a href="/docs/">Docs</a>
        </nav>
    </header>
    <main>
        {{ content | safe }}
    </main>
    <footer>
        <p>&copy; {{ now.year }} {{ site.name }}. Built with Metupy.</p>
    </footer>
</body>
</html>'''
        (theme_path / 'templates' / 'base.html').write_text(
            base_template,
            encoding='utf-8'
        )

        default_template = '''{% extends "base.html" %}

{% block content %}
<main>
    <h1>{{ title }}</h1>
    {{ content | safe }}
</main>
{% endblock %}'''
        (theme_path / 'templates' / 'default.html').write_text(
            default_template,
            encoding='utf-8'
        )

        theme = Theme(theme_name, theme_path)
        theme.load()
        self.themes[theme_name] = theme
        self.active_theme = theme

    def get_theme_settings(self) -> Dict[str, Any]:
        """
        Get current theme settings.

        Returns:
            Active theme settings dictionary.
        """
        if self.active_theme:
            return self.active_theme.get_settings()
        return {}

    def get_current_theme(self) -> Optional[Theme]:
        """
        Get current active theme.

        Returns:
            Active Theme instance or None.
        """
        return self.active_theme

    def get_theme(self, name: str) -> Optional[Theme]:
        """
        Get theme by name.

        Args:
            name: Theme name.

        Returns:
            Theme instance or None.
        """
        return self.themes.get(name)

    def list_themes(self) -> List[str]:
        """
        List all registered themes.

        Returns:
            List of theme names.
        """
        return list(self.themes.keys())

    def get_partial(self, name: str) -> Optional[Path]:
        """
        Get partial from active theme.

        Args:
            name: Partial name.

        Returns:
            Path to partial or None.
        """
        if self.active_theme:
            return self.active_theme.get_partial(name)
        return None

    def get_static_file(self, name: str) -> Optional[Path]:
        """
        Get static file from active theme.

        Args:
            name: Static file name.

        Returns:
            Path to static file or None.
        """
        if self.active_theme:
            return self.active_theme.get_static_file(name)
        return None