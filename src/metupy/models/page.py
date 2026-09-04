"""
Page model for Metupy.

Stores CMS pages with UUID4 primary keys.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from peewee import (
    CharField,
    TextField,
    BooleanField,
    IntegerField,
    ForeignKeyField,
    UUIDField,
    DateTimeField,
)

from metupy.models.base import BaseModel


class PageModel(BaseModel):
    """CMS page model."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    title = CharField(max_length=200)
    slug = CharField(unique=True, max_length=200)
    content = TextField()
    template = CharField(max_length=100, default='default.html')
    status = CharField(max_length=20, default='draft')
    author_id = UUIDField(null=True)
    parent_id = UUIDField(null=True)
    order = IntegerField(default=0)
    is_homepage = BooleanField(default=False)
    meta_description = CharField(max_length=500, null=True)
    meta_keywords = CharField(max_length=500, null=True)
    content_type = CharField(max_length=50, default='page')
    featured_image = CharField(max_length=500, null=True)
    is_published = BooleanField(default=False)
    published_at = DateTimeField(null=True)

    class Meta:
        table_name = 'pages'

    def publish(self) -> None:
        """Publish the page."""
        self.status = 'published'
        self.is_published = True
        self.published_at = datetime.now()
        self.save()

    def unpublish(self) -> None:
        """Unpublish the page."""
        self.status = 'draft'
        self.is_published = False
        self.published_at = None
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert page to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            'id': str(self.id),
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'template': self.template,
            'status': self.status,
            'author_id': str(self.author_id) if self.author_id else None,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'order': self.order,
            'is_homepage': self.is_homepage,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'content_type': self.content_type,
            'featured_image': self.featured_image,
            'is_published': self.is_published,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }