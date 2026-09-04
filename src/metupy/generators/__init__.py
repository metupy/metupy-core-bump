"""
Generators for Metupy.

Lazy imports for generator classes.
"""

__all__ = [
    "StaticGenerator",
]


def __getattr__(name: str):
    """
    Lazy import for generator classes.

    Args:
        name: Attribute name.

    Returns:
        Generator class or raises AttributeError.
    """
    if name == "StaticGenerator":
        from metupy.generators.static_generator import StaticGenerator
        return StaticGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")