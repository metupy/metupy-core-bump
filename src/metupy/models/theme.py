"""
Theme model for Metupy.

Stores theme metadata with UUID4 primary keys.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from peewee import CharField, TextField, BooleanField, UUIDField

from metupy.models.base import BaseModel


class ThemeModel(BaseModel):
    """Theme metadata model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(unique=True, max_length=200)
    version = CharField(max_length=50)
    description = TextField()
    author = CharField(max_length=200)
    is_active = BooleanField(default=False)
    settings = TextField(null=True)
    preview_image = CharField(max_length=500, null=True)
    tags = TextField(null=True)

    class Meta:
        table_name = 'themes'

    def get_settings(self) -> Dict[str, Any]:
        """
        Get theme settings.

        Returns:
            Settings dictionary.
        """
        if self.settings:
            try:
                return json.loads(self.settings)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_tags(self) -> List[str]:
        """
        Get theme tags.

        Returns:
            List of tag strings.
        """
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert theme to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'is_active': self.is_active,
            'settings': self.get_settings(),
            'preview_image': self.preview_image,
            'tags': self.get_tags(),
        }