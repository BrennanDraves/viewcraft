"""Types for viewcraft."""

from typing import Any, Protocol, TypeVar

from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.views import View

ViewT = TypeVar("ViewT", bound=View)

class ComponentProtocol(Protocol):
    """Protocol defining the interface for view components."""

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Call during view setup before dispatch."""
        ...

    def dispatch(
            self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse | None:
        """
        Call during request dispatch.

        Return HttpResponse to short-circuit the view, or None to continue.
        """
        ...

    def get_queryset(self, queryset: QuerySet) -> QuerySet:
        """Modify the queryset before it's used."""
        ...

    def get_context_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """Modify the template context before rendering."""
        ...

    def form_valid(self, form: Any) -> HttpResponse | None:
        """Call when form is valid in form views."""
        ...

    def form_invalid(self, form: Any) -> HttpResponse | None:
        """Call when form is invalid in form views."""
        ...
