"""
Core view functionality for the viewcraft package.

This module provides the ComponentMixin class which enables Django views
to use the viewcraft component system. It handles component initialization,
hook execution, and method interception to create a composable view system.

The mixin can be applied to any Django class-based view to add component
support, allowing views to be built from reusable, modular pieces of
functionality.
"""

from typing import Any, ClassVar, Generic, List, Optional, TypeVar, cast

from django.http import HttpRequest, HttpResponse

from .components import Component, ComponentConfig
from .enums import HookMethod
from .exceptions import ComponentError
from .types import ViewT

T = TypeVar('T')  # For return type of hook methods

class ComponentMixin(Generic[ViewT]):
    """
    Mixin that adds component support to Django class-based views.

    ComponentMixin provides the infrastructure for using viewcraft components
    in Django views. It handles component initialization, method interception,
    and hook execution, allowing views to be composed from reusable pieces
    of functionality.

    Components are initialized lazily when first needed and maintain their
    state throughout the view's lifecycle. The mixin ensures that components
    are executed in the correct order and that all hooks are properly called.

    Attributes:
        components (ClassVar[List[ComponentConfig]]): List of component configurations
            for the view
        _initialized_components (Optional[List[Component]]): Internal list of
            initialized component instances
        _setup_done (bool): Flag indicating if component setup has completed

    Example:
        >>> class MyListView(ComponentMixin, ListView):
        ...     components = [
        ...         FilterConfig(field='status', value='active'),
        ...         PaginationConfig(per_page=20)
        ...     ]
    """

    components: ClassVar[List[ComponentConfig]] = []
    _initialized_components: Optional[List[Component]] = None
    _setup_done: bool = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._setup_done = False

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Override of Django's dispatch method to ensure component setup.

        Ensures that components are properly initialized before any view
        processing occurs.

        Args:
            request: The current HTTP request
            *args: Positional arguments from the URL configuration
            **kwargs: Keyword arguments from the URL configuration

        Returns:
            HttpResponse: The response from the view
        """
        if not self._setup_done:
            self._do_setup(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def _do_setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """
        Initialize components and perform setup.

        Called before any view processing to ensure components are ready.
        This method is idempotent and will only perform initialization once.

        Args:
            request: The current HTTP request
            *args: Positional arguments from URL configuration
            **kwargs: Keyword arguments from URL configuration
        """
        # Initialize components if needed
        if self._initialized_components is None:
            self._initialize_components()

        # Mark setup as done
        self._setup_done = True

    def _initialize_components(self) -> None:
        """
        Create component instances from their configurations.

        Instantiates all configured components in the correct order, handling
        any initialization errors appropriately.

        Raises:
            ComponentError: If component initialization fails
        """
        try:
            view = cast(ViewT, self)
            self._initialized_components = []

            components = [config.build_component(view) for config in self.components]
            sorted_components = sorted(
                components, key=lambda c: getattr(c, '_sequence', 0)
            )
            self._initialized_components = sorted_components
        except Exception as e:
            raise ComponentError(f"Failed to initialize components: {str(e)}") from e

    def _run_hook_chain(
        self,
        hook: HookMethod,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute a complete chain of hooks for a given method.

        Processes all component hooks in the correct order:
        1. Pre-hooks (can short-circuit execution)
        2. Original method
        3. Process hooks (can modify the result)
        4. Post hooks (cleanup)

        Args:
            hook: The hook method being executed
            *args: Original method arguments
            **kwargs: Original method keyword arguments

        Returns:
            Any: The result after all hook processing
        """
        # Ensure setup has run
        if not self._setup_done:
            self._do_setup(kwargs.get('request', None), *args, **kwargs)

        if not self._initialized_components:
            return self._call_parent_method(hook, *args, **kwargs)

        # Run pre hooks - allow early returns
        for component in self._initialized_components:
            if pre_hook := component.get_pre_hook(hook):
                early_return = pre_hook()
                if early_return is not None:
                    return early_return

        # Call parent method with original args
        result = self._call_parent_method(hook, *args, **kwargs)

        # Run process hooks
        for component in self._initialized_components:
            if process_hook := component.get_process_hook(hook):
                result = process_hook(result)

        # Run post hooks
        for component in self._initialized_components:
            if post_hook := component.get_post_hook(hook):
                post_hook()

        return result

    def _call_parent_method(self, hook: HookMethod, *args: Any, **kwargs: Any) -> Any:
        """
        Call the original method implementation from the parent class.

        Attempts to call the parent class's implementation of the hooked method,
        handling cases where the method might not exist.

        Args:
            hook: The hook method being executed
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Any: The result of the parent method

        Raises:
            NotImplementedError: If the parent class doesn't implement the method
        """
        try:
            parent_method = getattr(super(), hook.value)
            return parent_method(*args, **kwargs)
        except AttributeError:
            # If parent doesn't implement the method, raise NotImplementedError
            # This matches Django's default behavior
            raise NotImplementedError(
                f"Method {hook.value} not implemented on parent class"
            ) from None

    def __getattribute__(self, name: str) -> Any:
        """
        Intercept method calls to inject hook processing.

        Wraps view methods to enable hook processing while maintaining transparency
        to the rest of the Django framework. Only intercepts methods that have
        corresponding hook points.

        Args:
            name: Name of the attribute being accessed

        Returns:
            Any: Either the original attribute or a hook-wrapped method
        """
        # First check if this is a hook method without calling super()
        try:
            if not name.startswith('_'):  # Don't process private methods
                hook_method = HookMethod(name)
                # Get the attribute via super() only after we know it's a hook
                super().__getattribute__(name)

                def wrapped(*args: Any, **kwargs: Any) -> Any:
                    return self._run_hook_chain(hook_method, *args, **kwargs)

                return wrapped
        except ValueError:
            pass

        # If it's not a hook method or is private, get the attribute normally
        return super().__getattribute__(name)
