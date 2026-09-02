# metupy/models/theme.py
"""Theme model dengan UUID."""

from peewee import CharField, TextField, BooleanField, UUIDField
from metupy.models.base import BaseModel
import uuid
import json

class ThemeModel(BaseModel):
    """Theme model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(unique=True, max_length=200)
    version = CharField(max_length=50)
    description = TextField()
    author = CharField(max_length=200)
    is_active = BooleanField(default=False)
    settings = TextField(null=True)  # JSON string
    
    # Additional fields
    preview_image = CharField(max_length=500, null=True)
    tags = TextField(null=True)  # JSON array
    dependencies = TextField(null=True)  # JSON array
    
    class Meta:
        table_name = 'themes'
        
    def get_settings(self) -> dict:
        """Get settings as dictionary."""
        if self.settings:
            return json.loads(self.settings)
        return {}
        
    def set_settings(self, settings: dict):
        """Set settings from dictionary."""
        self.settings = json.dumps(settings)
        self.save()
        
    def get_tags(self) -> list:
        """Get tags list."""
        if self.tags:
            return json.loads(self.tags)
        return []
        
    def to_dict(self):
        """Convert to dictionary."""
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }