"""
Base database models for Metupy.

Provides database connection management and base model
with UUID4 primary keys.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from peewee import (
    Model,
    SqliteDatabase,
    PostgresqlDatabase,
    MySQLDatabase,
    DateTimeField,
    UUIDField,
)


class DatabaseManager:
    """Manage database connections."""

    def __init__(self, config):
        """
        Initialize DatabaseManager.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.database = self._create_database()

    def _create_database(self):
        """
        Create database connection based on engine.

        Returns:
            Database connection object.
        """
        engine = getattr(self.config, 'DB_ENGINE', 'sqlite')

        if engine == 'sqlite':
            db_path = Path(getattr(self.config, 'DB_PATH', Path.home() / '.metupy' / 'data' / 'metupy.db'))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return SqliteDatabase(str(db_path))

        elif engine == 'postgresql':
            return PostgresqlDatabase(
                getattr(self.config, 'DB_NAME', 'metupy_db'),
                user=getattr(self.config, 'DB_USER', 'root'),
                password=getattr(self.config, 'DB_PASS', ''),
                host=getattr(self.config, 'DB_HOST', 'localhost'),
                port=getattr(self.config, 'DB_PORT', 5432),
            )

        elif engine == 'mysql':
            return MySQLDatabase(
                getattr(self.config, 'DB_NAME', 'metupy_db'),
                user=getattr(self.config, 'DB_USER', 'root'),
                password=getattr(self.config, 'DB_PASS', ''),
                host=getattr(self.config, 'DB_HOST', 'localhost'),
                port=getattr(self.config, 'DB_PORT', 3306),
            )

        raise ValueError(f"Unsupported database engine: {engine}")

    def connect(self) -> None:
        """Connect to database."""
        self.database.connect()

    def close(self) -> None:
        """Close database connection."""
        self.database.close()

    def create_tables(self, models: List) -> None:
        """
        Create database tables.

        Args:
            models: List of model classes.
        """
        self.database.create_tables(models)

    def drop_tables(self, models: List) -> None:
        """
        Drop database tables.

        Args:
            models: List of model classes.
        """
        self.database.drop_tables(models)


# Global database instance
db: Optional[DatabaseManager] = None


def init_database(config) -> DatabaseManager:
    """
    Initialize global database manager.

    Args:
        config: Configuration object.

    Returns:
        DatabaseManager instance.
    """
    global db
    db = DatabaseManager(config)
    return db


class BaseModel(Model):
    """Base model with UUID4 primary key."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db.database if db else None

    def save(self, *args, **kwargs) -> None:
        """Save model with updated timestamp."""
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Returns:
            Dictionary representation of model.
        """
        data = {}
        for field in self._meta.fields:
            value = getattr(self, field)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            data[field] = value
        return data