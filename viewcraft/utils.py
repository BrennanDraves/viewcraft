from typing import Any, Dict, Optional
from urllib.parse import urlencode

from django.http import HttpRequest


def modify_query_params(request: HttpRequest, params: Dict[str, Optional[Any]]) -> str:
    """
    Return URL with modified query parameters.

    Args:
        request: The current request
        params: Dict of parameters to update. If value is None, parameter is removed.

    Returns:
        URL string with updated query parameters
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
    """Mixin to add URL modification capabilities to components."""

    def get_url_with_params(self: Any, params: Dict[str, Optional[Any]]) -> str:
        """
        Get current URL with modified parameters.
        If a parameter value is None, that parameter is removed.
        """
        return modify_query_params(self._view.request, params)
