# metupy/core/json_storage.py
"""JSON Storage untuk Metupy."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiofiles
import asyncio

class JSONStorage:
    """Generic JSON storage manager."""
    
    def __init__(self, engine):
        self.engine = engine
        self.data_dir = Path(engine.config.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def save(self, filename: str, data: Any) -> bool:
        """Save data to JSON file."""
        try:
            file_path = self.data_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False, default=str))
                
            return True
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return False
            
    async def load(self, filename: str) -> Optional[Any]:
        """Load data from JSON file."""
        try:
            file_path = self.data_dir / filename
            
            if not file_path.exists():
                return None
                
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            print(f"Error loading from JSON: {e}")
            return None
            
    async def delete(self, filename: str) -> bool:
        """Delete JSON file."""
        try:
            file_path = self.data_dir / filename
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting JSON file: {e}")
            return False
            
    async def list_files(self, pattern: str = "*.json") -> List[Path]:
        """List JSON files."""
        return list(self.data_dir.glob(pattern))
        
    async def clear(self):
        """Clear all JSON files."""
        try:
            for file in self.data_dir.glob("*.json"):
                file.unlink()
        except Exception as e:
            print(f"Error clearing JSON files: {e}")
            
    def sync_save(self, filename: str, data: Any) -> bool:
        """Synchronous save."""
        try:
            file_path = self.data_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
            return True
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return False
            
    def sync_load(self, filename: str) -> Optional[Any]:
        """Synchronous load."""
        try:
            file_path = self.data_dir / filename
            if not file_path.exists():
                return None
            return json.loads(file_path.read_text())
        except Exception as e:
            print(f"Error loading from JSON: {e}")
            return None


class CommentJSONStorage:
    """JSON Storage khusus untuk comments."""
    
    def __init__(self, engine):
        self.engine = engine
        self.data_dir = Path(engine.config.DATA_DIR) / 'comments'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def save_comments(self, post_slug: str, comments: List[Dict]) -> bool:
        """Save comments to JSON."""
        try:
            file_path = self.data_dir / f"{post_slug}.json"
            
            data = {
                'post_slug': post_slug,
                'last_updated': datetime.now().isoformat(),
                'total_comments': len(comments),
                'comments': comments,
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False, default=str))
                
            return True
        except Exception as e:
            print(f"Error saving comments: {e}")
            return False
            
    async def load_comments(self, post_slug: str) -> List[Dict]:
        """Load comments from JSON."""
        try:
            file_path = self.data_dir / f"{post_slug}.json"
            
            if not file_path.exists():
                return []
                
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                
            return data.get('comments', [])
        except Exception as e:
            print(f"Error loading comments: {e}")
            return []
            
    async def save_all_comments(self, comments_data: Dict[str, List[Dict]]):
        """Save all comments."""
        for post_slug, comments in comments_data.items():
            await self.save_comments(post_slug, comments)