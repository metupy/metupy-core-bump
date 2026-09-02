# metupy/config.py
"""Configuration loader for Metupy.

Loads configuration from pymconfig.py file in the project root.
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """Loads and manages Metupy configuration."""
    
    def __init__(self, config_file: str = "pymconfig.py"):
        self.config_file = config_file
        self.config_path = self._find_config_file()
        self._config = {}
        
        # Only load if config file exists
        if self.config_path:
            self._load_config()
        else:
            # Set default values for when config doesn't exist yet
            self._set_default_config()
        
    def _find_config_file(self) -> Optional[Path]:
        """Find pymconfig.py in current directory or parent directories."""
        current_dir = Path.cwd()
        
        # Check current directory first
        config_path = current_dir / self.config_file
        if config_path.exists():
            return config_path
            
        # Check parent directories
        for parent in current_dir.parents:
            config_path = parent / self.config_file
            if config_path.exists():
                return config_path
                
        return None
        
    def _set_default_config(self):
        """Set default configuration values."""
        self._config = {
            'SITE_NAME': 'Metupy Site',
            'SITE_VERSION': '1.0.0',
            'SITE_DESCRIPTION': 'Built with Metupy SSG',
            'SITE_AUTHOR': 'Unknown',
            'SITE_KEYWORDS': ['metupy', 'ssg'],
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
            # Server (Preview/Serve) - Port 3155
            'DEV_HOST': 'localhost',
            'DEV_PORT': 3155,
            'DEV_DEBUG': True,
            'DEV_LIVE_RELOAD': True,
            'DEV_OPEN_BROWSER': True,
            # Studio - Port 3154
            'STUDIO_ENABLED': True,
            'STUDIO_HOST': 'localhost',
            'STUDIO_PORT': 3154,
            'STUDIO_AUTO_OPEN': True,
            'STUDIO_REQUIRE_LOGIN': True,
            'DB_ENGINE': 'sqlite',
            'DB_HOST': 'localhost',
            'DB_PORT': 5432,
            'DB_USER': 'root',
            'DB_PASS': '',
            'DB_NAME': 'metupy_db',
            'DB_PATH': Path.cwd() / 'data' / 'metupy.db',
            'CACHE_ENABLED': True,
            'CACHE_TYPE': 'redis',
            'CACHE_HOST': 'localhost',
            'CACHE_PORT': 6379,
            'CACHE_DB': 0,
            'CACHE_PASSWORD': None,
            'CACHE_TTL': 3600,
            'CACHE_PREFIX': 'metupy',
            'SECRET_KEY': 'dev-secret-key-change-in-production',
            'TOKEN_EXPIRY': 3600,
            'ALLOWED_HOSTS': ['localhost', '127.0.0.1'],
            'CSRF_ENABLED': True,
            'CORS_ENABLED': True,
            'CORS_ORIGINS': ['*'],
            'MARKDOWN_EXTENSIONS': ['extra', 'codehilite', 'toc', 'tables', 'fenced_code'],
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
                'storage': 'redis',
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
        
    def _load_config(self):
        """Load configuration from pymconfig.py."""
        # Add config file directory to Python path
        config_dir = str(self.config_path.parent)
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
            
        # Load module
        spec = importlib.util.spec_from_file_location(
            "pymconfig",
            self.config_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Extract all UPPERCASE variables
        self._config = {
            key: value
            for key, value in module.__dict__.items()
            if key.isupper() and not key.startswith('_')
        }
        
        # Set base directory
        self._config['BASE_DIR'] = self.config_path.parent
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
        
    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to configuration values."""
        if name in self._config:
            return self._config[name]
        # Return None for missing attributes instead of raising
        return None
        
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self._config[key]
        
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return key in self._config
        
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()
        
    def update(self, **kwargs):
        """Update configuration values."""
        self._config.update(kwargs)
        
    def reload(self):
        """Reload configuration from file."""
        self.config_path = self._find_config_file()
        if self.config_path:
            self._config.clear()
            self._load_config()
        
    def validate(self) -> bool:
        """Validate required configuration values."""
        required = [
            'SITE_NAME',
            'SITE_URL',
            'OUTPUT_DIR',
            'CONTENT_DIR',
        ]
        
        missing = [key for key in required if key not in self._config]
        
        if missing:
            print(f"Warning: Missing configuration: {', '.join(missing)}")
            return False
            
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config.copy()
        
    def __repr__(self) -> str:
        if self.config_path:
            return f"<ConfigLoader {self.config_path}>"
        return "<ConfigLoader (default config)>"


# Global config instance (lazy initialization)
_config_instance = None


def get_config() -> ConfigLoader:
    """Get or create config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance


def load_config(config_file: str = "pymconfig.py") -> ConfigLoader:
    """Load and return configuration."""
    global _config_instance
    _config_instance = ConfigLoader(config_file)
    return _config_instance


def reset_config():
    """Reset config instance."""
    global _config_instance
    _config_instance = None