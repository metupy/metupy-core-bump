"""
Widget model for Metupy.

Stores widget configuration with UUID4 primary keys.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from peewee import CharField, TextField, BooleanField, IntegerField, UUIDField

from metupy.models.base import BaseModel


class WidgetModel(BaseModel):
    """Widget configuration model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=200)
    widget_type = CharField(max_length=100)
    title = CharField(max_length=200, null=True)
    settings = TextField(null=True)
    is_active = BooleanField(default=True)
    area = CharField(max_length=50, default='sidebar')
    order = IntegerField(default=0)
    pages = TextField(null=True)

    class Meta:
        table_name = 'widgets'

    def get_settings(self) -> Dict[str, Any]:
        """
        Get widget settings.

        Returns:
            Settings dictionary.
        """
        if self.settings:
            try:
                return json.loads(self.settings)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_pages(self) -> List[str]:
        """
        Get pages where widget appears.

        Returns:
            List of page slugs.
        """
        if self.pages:
            try:
                return json.loads(self.pages)
            except json.JSONDecodeError:
                return []
        return []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert widget to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'widget_type': self.widget_type,
            'title': self.title,
            'settings': self.get_settings(),
            'is_active': self.is_active,
            'area': self.area,
            'order': self.order,
            'pages': self.get_pages(),
        }