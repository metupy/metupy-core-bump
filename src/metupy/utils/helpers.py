# metupy/utils/helpers.py
"""Utility helpers untuk Metupy."""

import re
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime


def slugify(text: str) -> str:
    """Convert text to slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def format_date(date: Union[str, datetime], format: str = '%Y-%m-%d') -> str:
    """Format date."""
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except:
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except:
                return str(date)
    if isinstance(date, datetime):
        return date.strftime(format)
    return str(date)


def read_file(file_path: Union[str, Path]) -> str:
    """Read file content (sync)."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.read_text(encoding='utf-8')


def write_file(file_path: Union[str, Path], content: str):
    """Write file content (sync)."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')


def ensure_directory(directory: Union[str, Path]):
    """Ensure directory exists."""
    if isinstance(directory, str):
        directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)


def copy_directory(source: Union[str, Path], destination: Union[str, Path]):
    """Copy directory (sync)."""
    if isinstance(source, str):
        source = Path(source)
    if isinstance(destination, str):
        destination = Path(destination)
        
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    elif source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def get_file_hash(file_path: Union[str, Path]) -> str:
    """Get file hash."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.stat().st_size


def humanize_size(size: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def parse_date(date_string: str) -> datetime:
    """Parse date string."""
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return datetime.now()


def truncate_text(text: str, length: int = 100) -> str:
    """Truncate text."""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'


def extract_tags(content: str) -> List[str]:
    """Extract hashtags."""
    return re.findall(r'#(\w+)', content)


def to_json(data: Any) -> str:
    """Convert to JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def from_json(json_string: str) -> Any:
    """Parse JSON string."""
    return json.loads(json_string)


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def safe_filename(filename: str) -> str:
    """Convert to safe filename."""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = ''.join(char for char in filename if ord(char) >= 32)
    filename = filename.strip('. ')
    return filename or 'unnamed'