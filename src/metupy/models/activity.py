"""
Activity log model for Metupy.

Stores user activity logs with UUID4 primary keys.
"""

import uuid
from typing import Any, Dict, Optional

from peewee import CharField, TextField, UUIDField, DateTimeField

from metupy.models.base import BaseModel


class ActivityLogModel(BaseModel):
    """Activity log model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = UUIDField(null=True)
    action = CharField(max_length=100)
    entity_type = CharField(max_length=50)
    entity_id = CharField(max_length=100, null=True)
    description = TextField()
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)
    metadata = TextField(null=True)
    severity = CharField(max_length=20, default='info')

    class Meta:
        table_name = 'activity_logs'

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert activity log to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
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