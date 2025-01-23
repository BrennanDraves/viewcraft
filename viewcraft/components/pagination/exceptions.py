"""
Pagination specific Exceptions.
"""

from django.core.paginator import InvalidPage

from viewcraft.exceptions import ViewcraftError


class PaginationError(ViewcraftError):
    """Base exception for pagination errors."""
    pass

class InvalidPageError(PaginationError, InvalidPage):
    """Invalid page number requested."""
    pass

class ConfigurationError(PaginationError):
    """Invalid pagination configuration."""
    pass
