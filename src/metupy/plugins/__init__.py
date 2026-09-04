"""
Built-in plugins for Metupy.

Plugins are loaded lazily to avoid circular imports
and unnecessary overhead.
"""

__all__ = [
    "SEOPlugin",
    "SitemapPlugin",
    "CommentsPlugin",
    "AnalyticsPlugin",
    "SearchPlugin",
    "RSSPlugin",
]


def __getattr__(name: str):
    """
    Lazy import for plugin classes.

    Args:
        name: Attribute name to resolve.

    Returns:
        Plugin class or raises AttributeError.

    Raises:
        AttributeError: If attribute is not a known plugin.
    """
    if name == "SEOPlugin":
        from metupy.plugins.seo import SEOPlugin
        return SEOPlugin
    elif name == "SitemapPlugin":
        from metupy.plugins.sitemap import SitemapPlugin
        return SitemapPlugin
    elif name == "CommentsPlugin":
        from metupy.plugins.comments import CommentsPlugin
        return CommentsPlugin
    elif name == "AnalyticsPlugin":
        from metupy.plugins.analytics import AnalyticsPlugin
        return AnalyticsPlugin
    elif name == "SearchPlugin":
        from metupy.plugins.search import SearchPlugin
        return SearchPlugin
    elif name == "RSSPlugin":
        from metupy.plugins.rss import RSSPlugin
        return RSSPlugin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")