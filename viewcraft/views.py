"""Views for viewcraft."""

from typing import TYPE_CHECKING, Any, cast

from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.views import View

if TYPE_CHECKING:
    from viewcraft import ComponentConfig, ComponentProtocol


class ComponentMixin:
    """Mixin that adds component functionality to views."""

    components: list["ComponentConfig"] = []
    _initialized_components: list["ComponentProtocol"] | None = None

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Initialize components and set up the view."""
        # Initialize components if not already done
        if self._initialized_components is None:
            self._initialized_components = [
                config.build_component(cast(View, self))
                for config in self.components
            ]

        # Call parent setup
        super().setup(request, *args, **kwargs)  # type: ignore

        # Run component setup
        for component in self._initialized_components:
            if hasattr(component, 'setup'):
                component.setup(request, *args, **kwargs)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Run components during dispatch phase."""
        assert self._initialized_components is not None

        # Run component dispatch
        for component in self._initialized_components:
            if hasattr(component, 'dispatch'):
                response = component.dispatch(request, *args, **kwargs)
                if response is not None:
                    return response

        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def get_queryset(self) -> QuerySet:
        """Apply component modifications to queryset."""
        assert self._initialized_components is not None

        queryset = super().get_queryset()  # type: ignore

        # Run component queryset modifications
        for component in self._initialized_components:
            if hasattr(component, 'get_queryset'):
                queryset = component.get_queryset(queryset)

        return cast(QuerySet, queryset)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Apply component modifications to context data."""
        assert self._initialized_components is not None

        context: dict[str, Any] = super().get_context_data(**kwargs)  # type: ignore

        # Run component context modifications
        for component in self._initialized_components:
            if hasattr(component, 'get_context_data'):
                context = component.get_context_data(context)

        return context

    def form_valid(self, form: Any) -> HttpResponse:
        """Handle valid form with components."""
        assert self._initialized_components is not None

        # Run component form_valid
        for component in self._initialized_components:
            if hasattr(component, 'form_valid'):
                response = component.form_valid(form)
                if response is not None:
                    return response

        return super().form_valid(form)  # type: ignore

    def form_invalid(self, form: Any) -> HttpResponse:
        """Handle invalid form with components."""
        assert self._initialized_components is not None

        # Run component form_invalid
        for component in self._initialized_components:
            if hasattr(component, 'form_invalid'):
                response = component.form_invalid(form)
                if response is not None:
                    return response

        return super().form_invalid(form)  # type: ignore
