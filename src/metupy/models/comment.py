"""
Comment model for Metupy.

Stores comments with UUID4 primary keys.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from peewee import CharField, TextField, BooleanField, IntegerField, UUIDField, DateTimeField

from metupy.models.base import BaseModel


class CommentModel(BaseModel):
    """Comment model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    post_slug = CharField(max_length=200)
    author_name = CharField(max_length=100)
    author_email = CharField(max_length=255)
    author_website = CharField(max_length=500, null=True)
    content = TextField()
    parent_id = UUIDField(null=True)
    is_approved = BooleanField(default=False)
    is_spam = BooleanField(default=False)
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    is_edited = BooleanField(default=False)
    edited_at = DateTimeField(null=True)
    approved_at = DateTimeField(null=True)
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)

    class Meta:
        table_name = 'comments'

    def approve(self) -> None:
        """Approve the comment."""
        self.is_approved = True
        self.is_spam = False
        self.approved_at = datetime.now()
        self.save()

    def mark_as_spam(self) -> None:
        """Mark comment as spam."""
        self.is_spam = True
        self.is_approved = False
        self.save()

    def like(self) -> None:
        """Increment likes."""
        self.likes += 1
        self.save()

    def dislike(self) -> None:
        """Increment dislikes."""
        self.dislikes += 1
        self.save()

    def edit(self, new_content: str) -> None:
        """
        Edit comment content.

        Args:
            new_content: New comment content.
        """
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.now()
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert comment to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'post_slug': self.post_slug,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'author_website': self.author_website,
            'content': self.content,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'is_approved': self.is_approved,
            'is_spam': self.is_spam,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'is_edited': self.is_edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }