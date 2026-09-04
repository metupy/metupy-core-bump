"""
Session model for Metupy.

Stores user sessions with UUID4 primary keys.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from peewee import CharField, TextField, BooleanField, UUIDField, DateTimeField

from metupy.models.base import BaseModel


class SessionModel(BaseModel):
    """User session model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = UUIDField(null=True)
    token = CharField(unique=True, max_length=500)
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)
    expires_at = DateTimeField()
    last_activity = DateTimeField(default=datetime.now)
    is_active = BooleanField(default=True)

    class Meta:
        table_name = 'sessions'

    def is_expired(self) -> bool:
        """
        Check if session is expired.

        Returns:
            True if expired.
        """
        return self.expires_at < datetime.now()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.save()

    def deactivate(self) -> None:
        """Deactivate session."""
        self.is_active = False
        self.save()

    @classmethod
    def create_session(
        cls,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration_hours: int = 24,
    ) -> 'SessionModel':
        """
        Create new session.

        Args:
            user_id: Optional user ID.
            ip_address: Client IP address.
            user_agent: Client user agent.
            duration_hours: Session duration.

        Returns:
            New SessionModel instance.
        """
        return cls.create(
            user_id=user_id,
            token=str(uuid.uuid4()),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(hours=duration_hours),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'token': self.token,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_active': self.is_active,
        }