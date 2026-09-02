# metupy/models/session.py
"""Session model dengan UUID."""

from peewee import CharField, TextField, DateTimeField, UUIDField, ForeignKeyField, BooleanField
from metupy.models.base import BaseModel
from metupy.models.user import User
import uuid
from datetime import datetime, timedelta

class SessionModel(BaseModel):
    """Session model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKeyField(User, backref='sessions', field='id')
    token = CharField(unique=True, max_length=500)
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)
    expires_at = DateTimeField()
    last_activity = DateTimeField(default=datetime.now)
    
    # Additional fields
    is_active = BooleanField(default=True)
    device_info = TextField(null=True)  # JSON string
    
    class Meta:
        table_name = 'sessions'
        
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return self.expires_at < datetime.now()
        
    def update_activity(self):
        """Update last activity."""
        self.last_activity = datetime.now()
        self.save()
        
    def deactivate(self):
        """Deactivate session."""
        self.is_active = False
        self.save()
        
    @classmethod
    def create_session(cls, user, ip_address=None, user_agent=None, duration_hours=24):
        """Create new session."""
        return cls.create(
            user=user,
            token=str(uuid.uuid4()),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(hours=duration_hours),
        )
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user': str(self.user.id),
            'token': self.token,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }