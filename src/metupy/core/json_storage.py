"""
JSON storage for Metupy.

Provides JSON file-based storage for various data types.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONStorage:
    """Generic JSON file storage."""

    def __init__(self, engine):
        """
        Initialize JSONStorage.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.data_dir = Path(getattr(engine.config, 'DATA_DIR', Path.home() / '.metupy' / 'data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: Any) -> bool:
        """
        Save data to JSON file.

        Args:
            filename: Output filename.
            data: Data to serialize.

        Returns:
            True if successful.
        """
        try:
            file_path = self.data_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding='utf-8'
            )
            return True
        except Exception as e:
            print(f"  JSON save error: {e}")
            return False

    def load(self, filename: str) -> Optional[Any]:
        """
        Load data from JSON file.

        Args:
            filename: File to load.

        Returns:
            Parsed data or None.
        """
        try:
            file_path = self.data_dir / filename
            if not file_path.exists():
                return None
            return json.loads(file_path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"  JSON load error: {e}")
            return None

    def delete(self, filename: str) -> bool:
        """
        Delete JSON file.

        Args:
            filename: File to delete.

        Returns:
            True if successful.
        """
        try:
            file_path = self.data_dir / filename
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception:
            return False

    def list_files(self, pattern: str = "*.json") -> List[Path]:
        """
        List JSON files.

        Args:
            pattern: Glob pattern.

        Returns:
            List of file paths.
        """
        return list(self.data_dir.glob(pattern))


class CommentJSONStorage:
    """JSON storage specifically for comments."""

    def __init__(self, engine):
        """
        Initialize CommentJSONStorage.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.data_dir = Path(getattr(engine.config, 'DATA_DIR', Path.home() / '.metupy' / 'data'))
        self.comments_dir = self.data_dir / 'comments'
        self.comments_dir.mkdir(parents=True, exist_ok=True)

    def save_comments(self, post_slug: str, comments: List[Dict]) -> bool:
        """
        Save comments for a post.

        Args:
            post_slug: Post slug.
            comments: List of comment dictionaries.

        Returns:
            True if successful.
        """
        try:
            file_path = self.comments_dir / f"{post_slug}.json"
            data = {
                'post_slug': post_slug,
                'comments': comments,
            }
            file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding='utf-8'
            )
            return True
        except Exception as e:
            print(f"  Comment save error: {e}")
            return False

    def load_comments(self, post_slug: str) -> List[Dict]:
        """
        Load comments for a post.

        Args:
            post_slug: Post slug.

        Returns:
            List of comment dictionaries.
        """
        try:
            file_path = self.comments_dir / f"{post_slug}.json"
            if not file_path.exists():
                return []
            data = json.loads(file_path.read_text(encoding='utf-8'))
            return data.get('comments', [])
        except Exception:
            return []