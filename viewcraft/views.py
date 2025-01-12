from typing import Any, ClassVar, Generic, List, Optional, TypeVar, cast

from django.http import HttpRequest, HttpResponse

from .components import Component, ComponentConfig
from .enums import HookMethod
from .types import ViewT

T = TypeVar('T')  # For return type of hook methods

class ComponentMixin(Generic[ViewT]):
    """Mixin that adds component functionality to Django views."""

    components: ClassVar[List[ComponentConfig]] = []
    _initialized_components: Optional[List[Component]] = None
    _setup_done: bool = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._setup_done = False

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Override dispatch to ensure setup runs first."""
        if not self._setup_done:
            self._do_setup(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def _do_setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Internal setup method that ensures component initialization."""
        # Initialize components if needed
        if self._initialized_components is None:
            self._initialize_components()

        # Mark setup as done
        self._setup_done = True

    def _initialize_components(self) -> None:
        """Initialize all components from their configs."""
        view = cast(ViewT, self)
        self._initialized_components = []

        sorted_configs = sorted(
            self.components,
            key=lambda c: getattr(c, '_sequence', 0)
        )
        for config in sorted_configs:
            component = config.build_component(view)
            self._initialized_components.append(component)

    def _run_hook_chain(
        self,
        hook: HookMethod,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute a chain of hooks for all components."""
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
        """Call the parent class's implementation of a method."""
        parent_method = getattr(super(), hook.value)  # type: ignore
        return parent_method(*args, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        """Intercept method calls to inject hook processing."""
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
