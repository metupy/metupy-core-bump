"""
Plugin model for Metupy.

Stores plugin metadata with UUID4 primary keys.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from peewee import CharField, TextField, BooleanField, UUIDField, DateTimeField

from metupy.models.base import BaseModel


class PluginModel(BaseModel):
    """Plugin metadata model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(unique=True, max_length=200)
    version = CharField(max_length=50)
    description = TextField()
    author = CharField(max_length=200)
    url = CharField(max_length=500, null=True)
    is_active = BooleanField(default=False)
    settings = TextField(null=True)
    category = CharField(max_length=50, default='general')
    dependencies = TextField(null=True)
    installed_at = DateTimeField(default=datetime.now)
    last_updated = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'plugins'

    def get_settings(self) -> Dict[str, Any]:
        """
        Get plugin settings as dictionary.

        Returns:
            Settings dictionary.
        """
        if self.settings:
            try:
                return json.loads(self.settings)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_settings(self, settings: Dict[str, Any]) -> None:
        """
        Set plugin settings.

        Args:
            settings: Settings dictionary.
        """
        self.settings = json.dumps(settings)
        self.save()

    def get_dependencies(self) -> List[str]:
        """
        Get plugin dependencies.

        Returns:
            List of dependency names.
        """
        if self.dependencies:
            try:
                return json.loads(self.dependencies)
            except json.JSONDecodeError:
                return []
        return []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert plugin to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'url': self.url,
            'is_active': self.is_active,
            'settings': self.get_settings(),
            'category': self.category,
            'dependencies': self.get_dependencies(),
            'installed_at': self.installed_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
        }