# metupy/utils/__init__.py
"""Utilities for Metupy."""

__all__ = [
    "slugify",
    "format_date",
    "read_file",
    "write_file",
    "copy_directory",
    "FileWatcher",
]

def __getattr__(name):
    if name in ["slugify", "format_date", "read_file", "write_file", "copy_directory"]:
        from metupy.utils.helpers import slugify, format_date, read_file, write_file, copy_directory
        return locals()[name]
    elif name == "FileWatcher":
        from metupy.utils.file_watcher import FileWatcher
        return FileWatcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")