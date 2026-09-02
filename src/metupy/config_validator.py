# metupy/config_validator.py
"""Configuration validation utilities."""

from pathlib import Path
from typing import Any, Dict, List


class ConfigValidator:
    """Validates Metupy configuration."""
    
    @staticmethod
    def validate_site_name(value: str) -> bool:
        """Validate site name."""
        return isinstance(value, str) and len(value) > 0
        
    @staticmethod
    def validate_site_url(value: str) -> bool:
        """Validate site URL."""
        return isinstance(value, str) and value.startswith(('http://', 'https://'))
        
    @staticmethod
    def validate_port(value: int) -> bool:
        """Validate port number."""
        return isinstance(value, int) and 0 < value < 65536
        
    @staticmethod
    def validate_path(value) -> bool:
        """Validate path."""
        return isinstance(value, (str, Path))
        
    @staticmethod
    def validate_plugins(value: List[str]) -> bool:
        """Validate plugins list."""
        return isinstance(value, list) and all(isinstance(p, str) for p in value)
        
    @classmethod
    def validate_all(cls, config: Dict[str, Any]) -> List[str]:
        """Validate all configuration values."""
        errors = []
        
        validators = {
            'SITE_NAME': cls.validate_site_name,
            'SITE_URL': cls.validate_site_url,
            'DEV_PORT': cls.validate_port,
            'STUDIO_PORT': cls.validate_port,
            'CONTENT_DIR': cls.validate_path,
            'OUTPUT_DIR': cls.validate_path,
            'ACTIVE_PLUGINS': cls.validate_plugins,
        }
        
        for key, validator in validators.items():
            if key in config:
                if not validator(config[key]):
                    errors.append(f"Invalid value for {key}: {config[key]}")
                    
        return errors