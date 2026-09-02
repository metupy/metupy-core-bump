# metupy/models/activity.py
"""Activity Log model dengan UUID."""

from peewee import CharField, TextField, DateTimeField, UUIDField, ForeignKeyField
from metupy.models.base import BaseModel
from metupy.models.user import User
import uuid

class ActivityLogModel(BaseModel):
    """Activity log model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKeyField(User, null=True, backref='activities', field='id')
    action = CharField(max_length=100)  # create, update, delete, login, logout, etc.
    entity_type = CharField(max_length=50)  # page, post, comment, user, etc.
    entity_id = CharField(max_length=100, null=True)  # UUID of entity
    description = TextField()
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)
    
    # Additional fields
    metadata = TextField(null=True)  # JSON string with additional data
    severity = CharField(max_length=20, default='info')  # info, warning, error, critical
    
    class Meta:
        table_name = 'activity_logs'
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user': str(self.user.id) if self.user else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'metadata': self.metadata,
            'severity': self.severity,
            'created_at': self.created_at.isoformat(),
        }