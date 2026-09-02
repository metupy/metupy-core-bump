# metupy/generators/__init__.py
"""Generators for Metupy."""

__all__ = [
    "StaticGenerator",
    "APIGenerator",
]

def __getattr__(name):
    if name == "StaticGenerator":
        from metupy.generators.static_generator import StaticGenerator
        return StaticGenerator
    elif name == "APIGenerator":
        from metupy.generators.api_generator import APIGenerator
        return APIGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")