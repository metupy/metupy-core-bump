"""
Renderers for Metupy.

Lazy imports to avoid circular dependencies.
"""

__all__ = [
    "PageRenderer",
    "BlogRenderer",
    "DocsRenderer",
    "SlidesRenderer",
]


def __getattr__(name: str):
    """
    Lazy import for renderer classes.

    Args:
        name: Attribute name.

    Returns:
        Renderer class or raises AttributeError.
    """
    if name == "PageRenderer":
        from metupy.renderers.page_renderer import PageRenderer
        return PageRenderer
    elif name == "BlogRenderer":
        from metupy.renderers.blog_renderer import BlogRenderer
        return BlogRenderer
    elif name == "DocsRenderer":
        from metupy.renderers.docs_renderer import DocsRenderer
        return DocsRenderer
    elif name == "SlidesRenderer":
        from metupy.renderers.slides_renderer import SlidesRenderer
        return SlidesRenderer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")