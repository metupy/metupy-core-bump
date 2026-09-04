"""
User model for Metupy.

Stores user accounts with UUID4 primary keys.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from peewee import CharField, TextField, BooleanField, DateTimeField, UUIDField

from metupy.models.base import BaseModel


class User(BaseModel):
    """User account model."""

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
    email_verified = BooleanField(default=False)
    verification_token = CharField(max_length=255, null=True)
    reset_token = CharField(max_length=255, null=True)
    reset_expires = DateTimeField(null=True)

    class Meta:
        table_name = 'users'

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using SHA-256 with salt.

        Args:
            password: Plain password.

        Returns:
            Salted hash string.
        """
        salt = secrets.token_hex(16)
        hashed = password + salt
        for _ in range(1000):
            hashed = hashlib.sha256(hashed.encode()).hexdigest()
        return f"{salt}${hashed}"

    def set_password(self, password: str) -> None:
        """
        Set user password.

        Args:
            password: Plain password.
        """
        self.password_hash = self.hash_password(password)

    def check_password(self, password: str) -> bool:
        """
        Verify password.

        Args:
            password: Plain password to check.

        Returns:
            True if password matches.
        """
        try:
            salt, original_hash = self.password_hash.split('$')
            hashed = password + salt
            for _ in range(1000):
                hashed = hashlib.sha256(hashed.encode()).hexdigest()
            return hashed == original_hash
        except (ValueError, AttributeError):
            return False

    def generate_verification_token(self) -> str:
        """
        Generate email verification token.

        Returns:
            Verification token string.
        """
        self.verification_token = str(uuid.uuid4())
        self.save()
        return self.verification_token

    def verify_email(self, token: str) -> bool:
        """
        Verify email with token.

        Args:
            token: Verification token.

        Returns:
            True if token matches.
        """
        if self.verification_token == token:
            self.email_verified = True
            self.verification_token = None
            self.save()
            return True
        return False

    def generate_reset_token(self) -> str:
        """
        Generate password reset token.

        Returns:
            Reset token string.
        """
        self.reset_token = str(uuid.uuid4())
        self.reset_expires = datetime.now() + timedelta(hours=1)
        self.save()
        return self.reset_token

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password with token.

        Args:
            token: Reset token.
            new_password: New password.

        Returns:
            True if reset successful.
        """
        if self.reset_token == token and self.reset_expires and self.reset_expires > datetime.now():
            self.set_password(new_password)
            self.reset_token = None
            self.reset_expires = None
            self.save()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary.

        Returns:
            Dictionary representation.
        """
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