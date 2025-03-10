"""
Search component exceptions.

Defines exceptions specific to the search component functionality.
"""

from viewcraft.exceptions import ViewcraftError


class SearchError(ViewcraftError):
    """Base exception class for search component errors."""
    pass


class SearchConfigError(SearchError):
    """Exception raised for invalid search configuration."""
    pass


class SearchQueryError(SearchError):
    """Exception raised for invalid search queries."""
    pass


class SearchEncodingError(SearchError):
    """Exception raised when encoding or decoding search parameters fails."""
    pass
