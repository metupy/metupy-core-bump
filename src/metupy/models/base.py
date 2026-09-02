# metupy/models/base.py
"""Base database models dengan UUID."""

from peewee import (
    Model, SqliteDatabase, PostgresqlDatabase, MySQLDatabase,
    CharField, TextField, DateTimeField, BooleanField, IntegerField,
    ForeignKeyField, ManyToManyField, CompositeKey, UUIDField
)
from datetime import datetime
from pathlib import Path
import uuid

class DatabaseManager:
    """Manages database connection."""
    
    def __init__(self, config):
        self.config = config
        self.database = self._create_database()
        
    def _create_database(self):
        """Create database connection."""
        engine = self.config.DB_ENGINE
        
        if engine == 'sqlite':
            db_path = self.config.DB_PATH
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return SqliteDatabase(str(db_path))
        elif engine == 'postgresql':
            return PostgresqlDatabase(
                self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASS,
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
            )
        elif engine == 'mysql':
            return MySQLDatabase(
                self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASS,
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
            )
        else:
            raise ValueError(f"Unsupported database engine: {engine}")
            
    def connect(self):
        """Connect to database."""
        self.database.connect()
        
    def close(self):
        """Close database connection."""
        self.database.close()
        
    def create_tables(self, models):
        """Create tables."""
        self.database.create_tables(models)
        
    def drop_tables(self, models):
        """Drop tables."""
        self.database.drop_tables(models)

# Global database instance
db = None

def init_database(config):
    """Initialize database."""
    global db
    db = DatabaseManager(config)
    return db

class BaseModel(Model):
    """Base model with UUID primary key."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        database = db.database if db else None
        
    def save(self, *args, **kwargs):
        """Override save to update timestamp."""
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
        
    def to_dict(self):
        """Convert model to dictionary."""
        data = {}
        for field in self._meta.fields:
            value = getattr(self, field)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            data[field] = value
        return data