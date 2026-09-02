# metupy/models/widget.py
"""Widget model dengan UUID."""

from peewee import CharField, TextField, BooleanField, UUIDField, IntegerField
from metupy.models.base import BaseModel
import uuid
import json

class WidgetModel(BaseModel):
    """Widget model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=200)
    widget_type = CharField(max_length=100)
    title = CharField(max_length=200, null=True)
    settings = TextField(null=True)  # JSON string
    is_active = BooleanField(default=True)
    
    # Additional fields
    area = CharField(max_length=50, default='sidebar')  # sidebar, footer, header, content
    order = IntegerField(default=0)
    pages = TextField(null=True)  # JSON array of page slugs where widget appears
    
    class Meta:
        table_name = 'widgets'
        
    def get_settings(self) -> dict:
        """Get settings as dictionary."""
        if self.settings:
            return json.loads(self.settings)
        return {}
        
    def set_settings(self, settings: dict):
        """Set settings from dictionary."""
        self.settings = json.dumps(settings)
        self.save()
        
    def get_pages(self) -> list:
        """Get pages where widget appears."""
        if self.pages:
            return json.loads(self.pages)
        return []
        
    def set_pages(self, pages: list):
        """Set pages where widget appears."""
        self.pages = json.dumps(pages)
        self.save()
        
    def to_dict(self):
        """Convert to dictionary."""
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }