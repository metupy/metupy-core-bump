# metupy/models/comment.py
"""Comment model dengan UUID."""

from peewee import (
    CharField, TextField, BooleanField, ForeignKeyField, 
    IntegerField, UUIDField, DateTimeField
)
from metupy.models.base import BaseModel
import uuid
import datetime

class CommentModel(BaseModel):
    """Comment model."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    post_slug = CharField(max_length=200)
    author_name = CharField(max_length=100)
    author_email = CharField(max_length=255)
    author_website = CharField(max_length=500, null=True)
    content = TextField()
    parent = ForeignKeyField('self', null=True, backref='replies', field='id')
    is_approved = BooleanField(default=False)
    is_spam = BooleanField(default=False)
    likes = IntegerField(default=0)
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)
    
    # Additional fields
    dislikes = IntegerField(default=0)
    is_edited = BooleanField(default=False)
    edited_at = DateTimeField(null=True)
    approved_by = ForeignKeyField('User', null=True, backref='approved_comments', field='id')
    approved_at = DateTimeField(null=True)
    
    class Meta:
        table_name = 'comments'
        
    def approve(self, user=None):
        """Approve comment."""
        self.is_approved = True
        self.is_spam = False
        self.approved_by = user
        self.approved_at = datetime.now()
        self.save()
        
    def mark_as_spam(self):
        """Mark as spam."""
        self.is_spam = True
        self.is_approved = False
        self.save()
        
    def like(self):
        """Like comment."""
        self.likes += 1
        self.save()
        
    def dislike(self):
        """Dislike comment."""
        self.dislikes += 1
        self.save()
        
    def edit(self, new_content: str):
        """Edit comment."""
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.now()
        self.save()
        
    def get_replies(self):
        """Get replies to this comment."""
        return CommentModel.select().where(
            CommentModel.parent == self,
            CommentModel.is_approved == True
        ).order_by(CommentModel.created_at)
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'post_slug': self.post_slug,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'author_website': self.author_website,
            'content': self.content,
            'parent': str(self.parent.id) if self.parent else None,
            'is_approved': self.is_approved,
            'is_spam': self.is_spam,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'is_edited': self.is_edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'approved_by': str(self.approved_by.id) if self.approved_by else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }