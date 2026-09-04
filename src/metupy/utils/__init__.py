"""
Utility functions for Metupy.

Lazy imports for utility helpers.
"""

__all__ = [
    "slugify",
    "format_date",
    "read_file",
    "write_file",
    "copy_directory",
    "ensure_directory",
]


def __getattr__(name: str):
    """
    Lazy import for utility functions.

    Args:
        name: Attribute name.

    Returns:
        Utility function or raises AttributeError.
    """
    from metupy.utils.helpers import (
        slugify,
        format_date,
        read_file,
        write_file,
        copy_directory,
        ensure_directory,
    )

    if name in __all__:
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")