"""
Configuration loader for Metupy.

Loads configuration from pymconfig.py file in the project root.
Uses global variables pattern similar to Django settings.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """Load and manage Metupy configuration from pymconfig.py."""

    def __init__(self, config_file: str = "pymconfig.py"):
        """
        Initialize configuration loader.

        Args:
            config_file: Name of the configuration file. Defaults to "pymconfig.py".
        """
        self.config_file = config_file
        self.config_path = self._find_config_file()
        self._config: Dict[str, Any] = {}

        if self.config_path:
            self._load_config()
        else:
            self._set_default_config()

    def _find_config_file(self) -> Optional[Path]:
        """
        Search for pymconfig.py in current and parent directories.

        Returns:
            Path to config file if found, None otherwise.
        """
        current_dir = Path.cwd()

        config_path = current_dir / self.config_file
        if config_path.exists():
            return config_path

        for parent in current_dir.parents:
            config_path = parent / self.config_file
            if config_path.exists():
                return config_path

        return None

    def _set_default_config(self) -> None:
        """Set default configuration values when no config file exists."""
        self._config = {
            'SITE_NAME': 'Metupy Site',
            'SITE_VERSION': '1.0.0',
            'SITE_DESCRIPTION': 'Built with Metupy SSG',
            'SITE_AUTHOR': 'Unknown',
            'SITE_KEYWORDS': ['metupy', 'ssg', 'static-site'],
            'SITE_LANG': 'en',
            'SITE_TIMEZONE': 'UTC',
            'SITE_URL': 'http://localhost:3155',
            'SITE_BASE_URL': '/',
            'SITE_CANONICAL_URL': 'http://localhost:3155/',
            'BASE_DIR': Path.cwd(),
            'CONTENT_DIR': Path.cwd() / 'content',
            'OUTPUT_DIR': Path.cwd() / 'public',
            'THEME_DIR': Path.cwd() / 'themes' / 'default',
            'ASSETS_DIR': Path.cwd() / 'content' / 'assets',
            'TEMPLATES_DIR': Path.cwd() / 'templates',
            'PLUGINS_DIR': Path.cwd() / 'plugins',
            'WIDGETS_DIR': Path.cwd() / 'widgets',
            'DATA_DIR': Path.cwd() / 'data',
            'ACTIVE_THEME': 'default',
            'ACTIVE_PLUGINS': [],
            'BUILD_MINIFY_HTML': False,
            'BUILD_MINIFY_CSS': False,
            'BUILD_MINIFY_JS': False,
            'BUILD_GENERATE_SITEMAP': True,
            'BUILD_GENERATE_FEED': True,
            'BUILD_CACHE_ENABLED': True,
            'BUILD_PRETTY_URLS': True,
            'DEV_HOST': 'localhost',
            'DEV_PORT': 3155,
            'DEV_DEBUG': True,
            'DEV_LIVE_RELOAD': True,
            'DEV_OPEN_BROWSER': True,
            'STUDIO_ENABLED': True,
            'STUDIO_HOST': 'localhost',
            'STUDIO_PORT': 3154,
            'STUDIO_AUTO_OPEN': True,
            'STUDIO_REQUIRE_LOGIN': True,
            'DB_ENGINE': 'sqlite',
            'DB_PATH': Path.cwd() / 'data' / 'metupy.db',
            'CACHE_ENABLED': False,
            'CACHE_TYPE': 'memory',
            'SECRET_KEY': 'dev-secret-key-change-in-production',
            'TOKEN_EXPIRY': 3600,
            'ALLOWED_HOSTS': ['localhost', '127.0.0.1'],
            'CSRF_ENABLED': True,
            'CORS_ENABLED': True,
            'CORS_ORIGINS': ['*'],
            'MARKDOWN_EXTENSIONS': ['extra', 'tables', 'fenced_code'],
            'MARKDOWN_EXTENSION_CONFIGS': {},
            'JINJA_EXTENSIONS': ['jinja2.ext.do', 'jinja2.ext.loopcontrols'],
            'SEO': {
                'generate_sitemap': True,
                'generate_robots': True,
                'generate_meta': True,
                'generate_og': True,
                'generate_twitter': True,
            },
            'COMMENTS': {
                'enabled': True,
                'storage': 'memory',
                'sync_time': '00:00',
                'moderation': True,
            },
            'SEARCH': {
                'enabled': True,
                'engine': 'lunr',
            },
            'DEBUG': True,
            'TESTING': False,
            'PRODUCTION': False,
        }

    def _load_config(self) -> None:
        """Load configuration from pymconfig.py file."""
        config_dir = str(self.config_path.parent)
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)

        try:
            # Try with encoding parameter (Python 3.11+)
            spec = importlib.util.spec_from_file_location(
                "pymconfig",
                self.config_path,
                encoding='utf-8'
            )
        except TypeError:
            # Fallback for older Python versions
            spec = importlib.util.spec_from_file_location(
                "pymconfig",
                self.config_path
            )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self._config = {
            key: value
            for key, value in module.__dict__.items()
            if key.isupper() and not key.startswith('_')
        }

        self._config['BASE_DIR'] = self.config_path.parent

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to configuration values."""
        if name in self._config:
            return self._config[name]
        return None

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to configuration values."""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Allow membership testing."""
        return key in self._config

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary of all configuration.
        """
        return self._config.copy()

    def update(self, **kwargs) -> None:
        """
        Update configuration values.

        Args:
            **kwargs: Key-value pairs to update.
        """
        self._config.update(kwargs)

    def reload(self) -> None:
        """Reload configuration from file."""
        self.config_path = self._find_config_file()
        if self.config_path:
            self._config.clear()
            self._load_config()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.
        """
        return self._config.copy()

    def __repr__(self) -> str:
        """String representation of ConfigLoader."""
        if self.config_path:
            return f"<ConfigLoader {self.config_path}>"
        return "<ConfigLoader (default config)>"


_config_instance: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """
    Get or create global config instance.

    Returns:
        ConfigLoader instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance


def load_config(config_file: str = "pymconfig.py") -> ConfigLoader:
    """
    Load configuration from specified file.

    Args:
        config_file: Path to configuration file.

    Returns:
        ConfigLoader instance.
    """
    global _config_instance
    _config_instance = ConfigLoader(config_file)
    return _config_instance


def reset_config() -> None:
    """Reset global config instance."""
    global _config_instance
    _config_instance = None