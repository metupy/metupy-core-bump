# metupy/models/page.py
"""Page model dengan UUID."""

from peewee import (
    CharField, TextField, BooleanField, IntegerField, 
    ForeignKeyField, UUIDField, DateTimeField
)
from metupy.models.base import BaseModel
from metupy.models.user import User
import uuid, datetime

class PageModel(BaseModel):
    """Page model for CMS."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    title = CharField(max_length=200)
    slug = CharField(unique=True, max_length=200)
    content = TextField()
    template = CharField(max_length=100, default='default.html')
    status = CharField(max_length=20, default='draft')  # draft, published, archived
    author = ForeignKeyField(User, backref='pages', null=True, field='id')
    parent = ForeignKeyField('self', null=True, backref='children', field='id')
    order = IntegerField(default=0)
    is_homepage = BooleanField(default=False)
    meta_description = CharField(max_length=500, null=True)
    meta_keywords = CharField(max_length=500, null=True)
    
    # Additional fields
    content_type = CharField(max_length=50, default='page')  # page, post, docs, etc.
    featured_image = CharField(max_length=500, null=True)
    is_published = BooleanField(default=False)
    published_at = DateTimeField(null=True)
    
    class Meta:
        table_name = 'pages'
        
    def publish(self):
        """Publish page."""
        self.status = 'published'
        self.is_published = True
        self.published_at = datetime.now()
        self.save()
        
    def unpublish(self):
        """Unpublish page."""
        self.status = 'draft'
        self.is_published = False
        self.published_at = None
        self.save()
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'template': self.template,
            'status': self.status,
            'author': str(self.author.id) if self.author else None,
            'parent': str(self.parent.id) if self.parent else None,
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