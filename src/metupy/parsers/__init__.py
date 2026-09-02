# metupy/parsers/__init__.py
"""Parsers for Metupy."""

# Lazy imports to avoid circular dependencies
__all__ = [
    "PYMParser",
    "MetupyMarkdownParser",
    "TemplateParser",
]

def __getattr__(name):
    if name == "PYMParser":
        from metupy.parsers.pym_parser import PYMParser
        return PYMParser
    elif name == "MetupyMarkdownParser":
        from metupy.parsers.markdown_parser import MetupyMarkdownParser
        return MetupyMarkdownParser
    elif name == "TemplateParser":
        from metupy.parsers.template_parser import TemplateParser
        return TemplateParser
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")