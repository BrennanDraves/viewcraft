from typing import Any, ClassVar, Generic, List, Optional, TypeVar, cast

from django.http import HttpRequest

from .components import Component, ComponentConfig
from .enums import HookMethod
from .types import ViewT

T = TypeVar('T')  # For return type of hook methods

class ComponentMixin(Generic[ViewT]):
    """Mixin that adds component functionality to Django views."""

    components: ClassVar[List[ComponentConfig]] = []
    _initialized_components: Optional[List[Component]] = None

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Initialize components during view setup."""
        super().setup(request, *args, **kwargs)  # type: ignore

        if self._initialized_components is None:
            self._initialize_components()

        self._run_hook_chain(HookMethod.SETUP, *args, **kwargs)

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
        parent_method = getattr(super(), hook.value)
        return parent_method(*args, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        """Intercept method calls to inject hook processing."""
        attr = super().__getattribute__(name)

        try:
            hook_method = HookMethod(name)
        except ValueError:
            return attr

        if name.startswith('_'):
            return attr

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return self._run_hook_chain(hook_method, *args, **kwargs)

        return wrapped
