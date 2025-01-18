"""
Utility functions and mixins for the viewcraft package.

Provides helper functions for URL manipulation and common mixins used
across components to enhance functionality.
"""

from typing import Any, Dict, Optional
from urllib.parse import urlencode

from django.http import HttpRequest


def modify_query_params(request: HttpRequest, params: Dict[str, Optional[Any]]) -> str:
    """
    Create a URL with modified query parameters based on the current request.

    Takes the current request's query parameters and updates them with the provided
    parameters. Parameters can be added, modified, or removed (by setting to None).

    Args:
        request: The current HTTP request
        params: Dictionary of parameters to update. If a value is None,
               the parameter is removed from the URL

    Returns:
        str: Full URL path with updated query parameters

    Example:
        >>> modify_query_params(request, {'page': '2', 'sort': None})
        '/current/path/?page=2'  # 'sort' parameter removed if it existed
    """
    # Start with current parameters
    current_params = dict(request.GET.items())

    # Update parameters
    for key, value in params.items():
        if value is None:
            current_params.pop(key, None)
        else:
            current_params[key] = str(value)

    # Build URL
    if current_params:
        return f"{request.path}?{urlencode(current_params)}"
    return request.path


class URLMixin:
    """
    Mixin providing URL manipulation capabilities to components.

    Adds methods for generating URLs with modified query parameters while
    maintaining the current request's context. Used by components that need
    to generate URLs for pagination, sorting, or filtering.
    """

    def get_url_with_params(self: Any, params: Dict[str, Optional[Any]]) -> str:
        """
        Generate URL with modified query parameters.

        Creates a new URL based on the current request's URL, updating or removing
        query parameters as specified.

        Args:
            params: Dictionary of parameters to update. If a value is None,
                   the parameter is removed from the URL

        Returns:
            str: URL string with updated query parameters

        Example:
            >>> self.get_url_with_params({'page': '2', 'sort': None})
            '/current/path/?page=2'  # 'sort' parameter removed if it existed
        """
        return modify_query_params(self._view.request, params)
