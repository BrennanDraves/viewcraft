"""
Exceptions for basic search component.
"""

from viewcraft.exceptions import ViewcraftError


class SearchError(ViewcraftError):
    """Base exception for search errors."""
    pass


class SearchConfigError(SearchError):
    """Error in search configuration."""
    pass


class SearchQueryError(SearchError):
    """Error in search query processing."""
    pass
