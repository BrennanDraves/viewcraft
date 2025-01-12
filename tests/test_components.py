import pytest
from django.db.models import QuerySet
from django.http import HttpResponse
from django.views.generic import View, TemplateView, CreateView, DetailView, UpdateView
from viewcraft import Component, ComponentConfig, ComponentMixin, HookMethod

from .factories import BlogPostFactory
from demo_app.models import BlogPost


class SimpleFilterComponent(Component):
    """A very simple component that just filters blog posts by status."""

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        filtered = queryset.filter(status='published')
        return filtered

class SimpleFilterConfig(ComponentConfig):
    def build_component(self, view):
        return SimpleFilterComponent(view)


class OrderedComponent(Component):
    """Component that logs its execution order."""
    def __init__(self, view, sequence: int, execution_log: list):
        super().__init__(view)
        self._sequence = sequence
        self.execution_log = execution_log

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        self.execution_log.append(self._sequence)
        return queryset

class OrderedComponentConfig(ComponentConfig):
    def __init__(self, sequence: int, execution_log: list):
        self._sequence = sequence
        self.execution_log = execution_log

    def build_component(self, view):
        return OrderedComponent(view, self._sequence, self.execution_log)

class PreHookComponent(Component):
    """Component that implements a pre hook with optional early return."""
    def __init__(self, view, should_return_early: bool = False):
        super().__init__(view)
        self.should_return_early = should_return_early

    def pre_get_queryset(self):
        if self.should_return_early:
            return QuerySet(model=self._view.model).none()

class PreHookConfig(ComponentConfig):
    def __init__(self, should_return_early: bool = False):
        self.should_return_early = should_return_early

    def build_component(self, view):
        return PreHookComponent(view, self.should_return_early)

class MultiHookComponent(Component):
    """Component that implements all three hook types."""
    def __init__(self, view, hook_log: list):
        super().__init__(view)
        self.hook_log = hook_log

    def pre_get_queryset(self):
        self.hook_log.append('pre')

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        self.hook_log.append('process')
        return queryset

    def post_get_queryset(self):
        self.hook_log.append('post')

class MultiHookConfig(ComponentConfig):
    def __init__(self, hook_log: list):
        self.hook_log = hook_log

    def build_component(self, view):
        return MultiHookComponent(view, self.hook_log)

# Tests
def test_basic_queryset_filtering(db, blog_posts, basic_view_class, rf):
    """Test that a simple component can filter a queryset."""
    # Set components BEFORE creating the view instance
    basic_view_class.components = [SimpleFilterConfig()]

    # Create request
    request = rf.get('/')

    # Create view and trigger initialization
    view = basic_view_class()

    # Make sure setup runs
    view._do_setup(request)

    # Set request and other attributes
    view.request = request
    view.args = []
    view.kwargs = {}

    # Get the queryset
    queryset = view.get_queryset()

    # Check that we got some posts
    assert queryset.exists(), "Queryset is empty!"

    # Check each post's status
    for post in queryset:
        assert post.status == 'published', f"Found non-published post with status: {post.status}"

def test_component_execution_order(db, basic_view_class, rf):
    """Test that components are executed in order based on their sequence."""
    execution_log = []
    basic_view_class.components = [
        OrderedComponentConfig(sequence=3, execution_log=execution_log),
        OrderedComponentConfig(sequence=1, execution_log=execution_log),
        OrderedComponentConfig(sequence=2, execution_log=execution_log),
    ]

    view = basic_view_class()
    view._do_setup(rf.get('/'))
    view.get_queryset()

    assert execution_log == [1, 2, 3], "Components did not execute in correct order"

def test_early_return_from_pre_hook(db, basic_view_class, rf, blog_posts):
    """Test that pre hooks can return early and skip further processing."""
    basic_view_class.components = [PreHookConfig(should_return_early=True)]

    view = basic_view_class()
    view._do_setup(rf.get('/'))
    queryset = view.get_queryset()

    assert queryset.count() == 0, "Early return queryset should be empty"

def test_hook_execution_order(db, basic_view_class, rf):
    """Test that pre, process, and post hooks execute in the correct order."""
    hook_log = []
    basic_view_class.components = [MultiHookConfig(hook_log)]

    view = basic_view_class()
    view._do_setup(rf.get('/'))
    view.get_queryset()

    assert hook_log == ['pre', 'process', 'post'], "Hooks did not execute in correct order"

def test_multiple_components_interaction(db, basic_view_class, rf, blog_posts):
    """Test that multiple components can work together on the same queryset."""
    class StatusFilterComponent(Component):
        def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
            return queryset.filter(status='published')

    class CategoryFilterComponent(Component):
        def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
            return queryset.filter(category='Technology')

    class StatusFilterConfig(ComponentConfig):
        def build_component(self, view):
            return StatusFilterComponent(view)

    class CategoryFilterConfig(ComponentConfig):
        def build_component(self, view):
            return CategoryFilterComponent(view)

    basic_view_class.components = [StatusFilterConfig(), CategoryFilterConfig()]

    view = basic_view_class()
    view._do_setup(rf.get('/'))
    queryset = view.get_queryset()

    for post in queryset:
        assert post.status == 'published'
        assert post.category == 'Technology'

def test_lazy_component_initialization(db, basic_view_class, rf):
    """Test that components are only initialized when needed."""
    initialization_count = 0

    class LazyComponent(Component):
        def __init__(self, view):
            nonlocal initialization_count
            initialization_count += 1
            super().__init__(view)

    class LazyConfig(ComponentConfig):
        def build_component(self, view):
            return LazyComponent(view)

    basic_view_class.components = [LazyConfig()]
    view = basic_view_class()

    assert initialization_count == 0, "Component should not be initialized yet"

    view._do_setup(rf.get('/'))
    assert initialization_count == 1, "Component should be initialized exactly once"

@pytest.fixture
def component_mixin_view():
    """A minimal view just using ComponentMixin for testing mixin behavior."""
    class SimpleView(ComponentMixin, View):
        def get(self, request, *args, **kwargs):
            return HttpResponse()
    return SimpleView

def test_dispatch_runs_setup(rf):
    """Test that dispatch actually triggers setup."""
    class TestDispatchView(ComponentMixin, TemplateView):  # Use TemplateView instead of View
        template_name = "dummy.html"  # Required by TemplateView
        called_setup = False

        def _do_setup(self, request, *args, **kwargs):
            self.called_setup = True
            super()._do_setup(request, *args, **kwargs)

    view = TestDispatchView.as_view()
    request = rf.get('/')
    response = view(request)
    assert response.status_code == 200

def test_multiple_hook_types(rf, basic_view_class, blog_posts):
    """Test that a component can handle multiple different hook types."""
    hook_calls = []

    class MultiHookComponent(Component):
        def pre_get_queryset(self):
            hook_calls.append('pre_get')

        def process_get_context_data(self, context):
            hook_calls.append('process_context')
            return context

        def post_get(self):
            hook_calls.append('post_get')

    class MultiConfig(ComponentConfig):
        def build_component(self, view):
            return MultiHookComponent(view)

    basic_view_class.components = [MultiConfig()]

    # Properly set up the view
    request = rf.get('/')
    view = basic_view_class()
    view.setup(request)  # This sets request and other attributes
    view.object_list = view.get_queryset()

    # Now trigger the hooks
    view.get_queryset()
    view.get_context_data()
    response = view.get(request)

    assert 'pre_get' in hook_calls
    assert 'process_context' in hook_calls
    assert 'post_get' in hook_calls

def test_component_initialization_happens_once(rf, basic_view_class):
    """Ensure components are only initialized once even with multiple calls."""
    init_count = 0

    class CountingComponent(Component):
        def __init__(self, view):
            nonlocal init_count
            init_count += 1
            super().__init__(view)

    class CountingConfig(ComponentConfig):
        def build_component(self, view):
            return CountingComponent(view)

    basic_view_class.components = [CountingConfig()]
    view = basic_view_class()

    # Call setup multiple times
    request = rf.get('/')
    view._do_setup(request)
    view._do_setup(request)
    view._do_setup(request)

    assert init_count == 1, "Components were initialized multiple times"

def test_hook_data_persistence(rf, basic_view_class):
    """Test that hook_data persists between different hook calls."""
    class DataStoringComponent(Component):
        def pre_get_queryset(self):
            self._hook_data['pre_called'] = True

        def process_get_queryset(self, queryset):
            assert self._hook_data.get('pre_called'), "Pre hook data not preserved"
            return queryset

    class DataConfig(ComponentConfig):
        def build_component(self, view):
            return DataStoringComponent(view)

    basic_view_class.components = [DataConfig()]
    view = basic_view_class()
    view._do_setup(rf.get('/'))
    view.get_queryset()

def test_invalid_hook_handling():
    """Test that trying to use a non-existent hook raises appropriate error."""
    with pytest.raises(ValueError):
        HookMethod('not_a_real_hook')

def test_component_error_handling(rf, basic_view_class):
    """Test that errors in components are properly propagated."""
    class ErrorComponent(Component):
        def process_get_queryset(self, queryset):
            raise ValueError("Test error")

    class ErrorConfig(ComponentConfig):
        def build_component(self, view):
            return ErrorComponent(view)

    basic_view_class.components = [ErrorConfig()]
    view = basic_view_class()
    view._do_setup(rf.get('/'))

    with pytest.raises(ValueError):
        view.get_queryset()

def test_component_inheritance(rf, basic_view_class):
    """Test that inherited component configurations work correctly."""
    class ChildView(basic_view_class):
        components = [SimpleFilterConfig()] + basic_view_class.components

    view = ChildView()
    view._do_setup(rf.get('/'))
    assert len(view._initialized_components) == len(ChildView.components)

def test_component_config_validation():
    """Test that component configs validate their parameters."""
    class ValidatedConfig(ComponentConfig):
        def __init__(self, required_param: str):
            self.required_param = required_param

        def build_component(self, view):
            if not self.required_param:
                raise ValueError("required_param cannot be empty")
            return SimpleFilterComponent(view)

    with pytest.raises(ValueError):
        ValidatedConfig("").build_component(None)

def test_component_config_inheritance():
    """Test that component configs can be inherited and extended."""
    class BaseConfig(ComponentConfig):
        def __init__(self, base_param: str):
            self.base_param = base_param

    class ExtendedConfig(BaseConfig):
        def build_component(self, view):
            assert self.base_param  # Verify inheritance
            return SimpleFilterComponent(view)

    config = ExtendedConfig("test")
    assert config.base_param == "test"

def test_all_hook_methods_called(rf, basic_view_class):
    """Test that all defined hook methods are properly called."""
    hook_calls = []

    class AllHooksComponent(Component):
        def pre_get(self): hook_calls.append('pre_get')
        def process_get(self, result):
            hook_calls.append('process_get')
            return result
        def post_get(self): hook_calls.append('post_get')
        def pre_get_queryset(self): hook_calls.append('pre_queryset')
        def process_get_queryset(self, qs):
            hook_calls.append('process_queryset')
            return qs
        def post_get_queryset(self): hook_calls.append('post_queryset')

    class AllHooksConfig(ComponentConfig):
        def build_component(self, view):
            return AllHooksComponent(view)

    basic_view_class.components = [AllHooksConfig()]
    view = basic_view_class()
    view.setup(rf.get('/'))
    view.get(view.request)

    expected_calls = [
        'pre_get', 'pre_queryset', 'process_queryset',
        'post_queryset', 'process_get', 'post_get'
    ]
    assert hook_calls == expected_calls

def test_hook_error_propagation(rf, basic_view_class):
    """Test that errors in hooks are properly propagated."""

    class ErrorInPreHookComponent(Component):
        def pre_get_queryset(self):
            raise ValueError("Pre hook error")

    class ErrorInProcessHookComponent(Component):
        def process_get_queryset(self, qs):
            raise ValueError("Process hook error")

    class ErrorInPostHookComponent(Component):
        def post_get_queryset(self):
            raise ValueError("Post hook error")

    # Create corresponding configs
    class ErrorInPreConfig(ComponentConfig):
        def build_component(self, view):
            return ErrorInPreHookComponent(view)

    class ErrorInProcessConfig(ComponentConfig):
        def build_component(self, view):
            return ErrorInProcessHookComponent(view)

    class ErrorInPostConfig(ComponentConfig):
        def build_component(self, view):
            return ErrorInPostHookComponent(view)

    # Test each type of hook error
    for config_class in [ErrorInPreConfig, ErrorInProcessConfig, ErrorInPostConfig]:
        basic_view_class.components = [config_class()]
        view = basic_view_class()
        view.setup(rf.get('/'))

        with pytest.raises(ValueError):
            view.get_queryset()

def test_integration_with_common_views():
    """Test integration with common Django view classes."""
    class CreateViewWithComponents(ComponentMixin, CreateView):
        model = BlogPost
        fields = ['title', 'body']

    class DetailViewWithComponents(ComponentMixin, DetailView):
        model = BlogPost

    class UpdateViewWithComponents(ComponentMixin, UpdateView):
        model = BlogPost
        fields = ['title']

    # Test each view type works with components
    for view_class in [CreateViewWithComponents, DetailViewWithComponents, UpdateViewWithComponents]:
        assert hasattr(view_class, 'components')
        assert hasattr(view_class, '_do_setup')
