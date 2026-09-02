# metupy/models/user.py
"""User model dengan UUID."""

from peewee import CharField, TextField, BooleanField, DateTimeField, UUIDField
from datetime import datetime, timedelta
from metupy.models.base import BaseModel
import hashlib
import uuid

class User(BaseModel):
    """User model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    username = CharField(unique=True, max_length=100)
    email = CharField(unique=True, max_length=255)
    password_hash = CharField(max_length=255)
    full_name = CharField(max_length=200, null=True)
    bio = TextField(null=True)
    avatar_url = CharField(max_length=500, null=True)
    website = CharField(max_length=500, null=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(null=True)
    
    # Additional fields
    email_verified = BooleanField(default=False)
    email_verification_token = CharField(max_length=255, null=True)
    password_reset_token = CharField(max_length=255, null=True)
    password_reset_expires = DateTimeField(null=True)
    
    class Meta:
        table_name = 'users'
        
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password."""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def set_password(self, password: str):
        """Set password."""
        self.password_hash = self.hash_password(password)
        
    def check_password(self, password: str) -> bool:
        """Check password."""
        return self.password_hash == self.hash_password(password)
        
    def generate_verification_token(self):
        """Generate email verification token."""
        self.email_verification_token = str(uuid.uuid4())
        self.save()
        return self.email_verification_token
        
    def verify_email(self, token: str) -> bool:
        """Verify email."""
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            self.save()
            return True
        return False
        
    def generate_password_reset_token(self):
        """Generate password reset token."""
        self.password_reset_token = str(uuid.uuid4())
        self.password_reset_expires = datetime.now() + timedelta(hours=1)
        self.save()
        return self.password_reset_token
        
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password."""
        if (
            self.password_reset_token == token and
            self.password_reset_expires > datetime.now()
        ):
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            self.save()
            return True
        return False
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'website': self.website,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }