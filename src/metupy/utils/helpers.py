"""
Utility helper functions for Metupy.

Provides common utilities used across the framework including
string manipulation, file operations, and data conversion.
"""

import re
import json
import shutil
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.

    Args:
        text: Input text to slugify.

    Returns:
        Slugified string (lowercase, hyphens instead of spaces).

    Example:
        >>> slugify("Hello World!")
        'hello-world'
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def format_date(date: Union[str, datetime], fmt: str = '%Y-%m-%d') -> str:
    """
    Format date to string.

    Args:
        date: Date as string or datetime object.
        fmt: Output date format.

    Returns:
        Formatted date string.
    """
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                return date

    if isinstance(date, datetime):
        return date.strftime(fmt)
    return str(date)


def read_file(file_path: Union[str, Path]) -> str:
    """
    Read file content synchronously.

    Args:
        file_path: Path to file.

    Returns:
        File content as string.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.read_text(encoding='utf-8')


def write_file(file_path: Union[str, Path], content: str) -> None:
    """
    Write content to file synchronously.

    Args:
        file_path: Path to output file.
        content: Content to write.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')


def ensure_directory(directory: Union[str, Path]) -> None:
    """
    Ensure directory exists, create if not.

    Args:
        directory: Directory path.
    """
    if isinstance(directory, str):
        directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)


def copy_directory(source: Union[str, Path], destination: Union[str, Path]) -> None:
    """
    Copy directory or file recursively.

    Args:
        source: Source path.
        destination: Destination path.
    """
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
    """
    Calculate MD5 hash of file.

    Args:
        file_path: Path to file.

    Returns:
        MD5 hash string.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def humanize_size(size: int) -> str:
    """
    Convert bytes to human-readable size.

    Args:
        size: Size in bytes.

    Returns:
        Human-readable size string.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def truncate_text(text: str, length: int = 100) -> str:
    """
    Truncate text to specified length.

    Args:
        text: Input text.
        length: Maximum length.

    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'


def extract_tags(content: str) -> List[str]:
    """
    Extract hashtags from text content.

    Args:
        content: Input text.

    Returns:
        List of hashtags found.
    """
    return re.findall(r'#(\w+)', content)


def to_json(data: Any) -> str:
    """
    Convert data to JSON string.

    Args:
        data: Python object to serialize.

    Returns:
        JSON string.
    """
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def from_json(json_string: str) -> Any:
    """
    Parse JSON string to Python object.

    Args:
        json_string: JSON string to parse.

    Returns:
        Parsed Python object.
    """
    return json.loads(json_string)


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries shallowly.

    Args:
        *dicts: Dictionaries to merge.

    Returns:
        Merged dictionary.
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.

    Args:
        dict1: Base dictionary.
        dict2: Dictionary to merge.

    Returns:
        Deep-merged dictionary.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def safe_filename(filename: str) -> str:
    """
    Convert string to safe filename.

    Args:
        filename: Input filename.

    Returns:
        Sanitized filename.
    """
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = ''.join(char for char in filename if ord(char) >= 32)
    filename = filename.strip('. ')
    return filename or 'unnamed'