# metupy/core/theme_manager.py
"""Theme Manager untuk Metupy."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class Theme:
    """Theme class."""
    
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.config = {}
        self.templates = {}
        self.static_files = {}
        self.layouts = {}
        self.components = {}
        
    def load(self):
        """Load theme configuration."""
        theme_file = self.path / 'theme.json'
        if theme_file.exists():
            try:
                self.config = json.loads(theme_file.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"  Error loading theme.json: {e}")
                self.config = {}
                
        # Load templates
        templates_dir = self.path / 'templates'
        if templates_dir.exists():
            for template in templates_dir.rglob('*.html'):
                relative = template.relative_to(templates_dir)
                self.templates[str(relative)] = template
                
        # Load static files
        static_dir = self.path / 'static'
        if static_dir.exists():
            for static_file in static_dir.rglob('*'):
                if static_file.is_file():
                    relative = static_file.relative_to(static_dir)
                    self.static_files[str(relative)] = static_file
                    
    def get_settings(self) -> Dict[str, Any]:
        """Get theme settings."""
        return self.config
        
    def get_template(self, name: str) -> Optional[Path]:
        """Get template by name."""
        return self.templates.get(name)
        
    def get_static_file(self, name: str) -> Optional[Path]:
        """Get static file by name."""
        return self.static_files.get(name)


class ThemeManager:
    """Manages themes."""
    
    def __init__(self, engine):
        self.engine = engine
        self.themes: Dict[str, Theme] = {}
        self.active_theme: Optional[Theme] = None
        
    async def load_theme(self):
        """Load active theme."""
        theme_name = getattr(self.engine.config, 'ACTIVE_THEME', 'default')
        theme_path = self.engine.theme_dir
        
        if theme_path.exists():
            theme = Theme(theme_name, theme_path)
            theme.load()
            self.themes[theme_name] = theme
            self.active_theme = theme
            print(f"  Theme loaded: {theme_name} ({len(theme.templates)} templates)")
        else:
            print(f"  Theme directory not found: {theme_path}")
            # Create default theme dir
            theme_path.mkdir(parents=True, exist_ok=True)
            (theme_path / 'templates').mkdir(exist_ok=True)
            (theme_path / 'static').mkdir(exist_ok=True)
            
            # Create theme.json
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
            
            theme = Theme(theme_name, theme_path)
            theme.load()
            self.themes[theme_name] = theme
            self.active_theme = theme
            
    def get_theme_settings(self) -> Dict[str, Any]:
        """Get current theme settings."""
        if self.active_theme:
            return self.active_theme.get_settings()
        return {}
        
    def get_current_theme(self) -> Optional[Theme]:
        """Get current theme."""
        return self.active_theme
        
    def list_themes(self) -> List[str]:
        """List all themes."""
        return list(self.themes.keys())
        
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self.themes.get(name)