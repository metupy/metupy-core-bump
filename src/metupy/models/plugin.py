# metupy/models/plugin.py
"""Plugin model dengan UUID."""

from peewee import CharField, TextField, BooleanField, DateTimeField, UUIDField
from metupy.models.base import BaseModel
import uuid
import json
import datetime

class PluginModel(BaseModel):
    """Plugin model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(unique=True, max_length=200)
    version = CharField(max_length=50)
    description = TextField()
    author = CharField(max_length=200)
    url = CharField(max_length=500, null=True)
    is_active = BooleanField(default=False)
    settings = TextField(null=True)  # JSON string
    
    # Additional fields
    category = CharField(max_length=50, default='general')
    dependencies = TextField(null=True)  # JSON array of plugin names
    required_by = TextField(null=True)  # JSON array of plugin names
    installed_at = DateTimeField(default=datetime.now)
    last_updated = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'plugins'
        
    def get_settings(self) -> dict:
        """Get settings as dictionary."""
        if self.settings:
            return json.loads(self.settings)
        return {}
        
    def set_settings(self, settings: dict):
        """Set settings from dictionary."""
        self.settings = json.dumps(settings)
        self.save()
        
    def update_settings(self, settings: dict):
        """Update settings."""
        current = self.get_settings()
        current.update(settings)
        self.set_settings(current)
        
    def get_dependencies(self) -> list:
        """Get dependencies list."""
        if self.dependencies:
            return json.loads(self.dependencies)
        return []
        
    def set_dependencies(self, dependencies: list):
        """Set dependencies list."""
        self.dependencies = json.dumps(dependencies)
        self.save()
        
    def to_dict(self):
        """Convert to dictionary."""
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }