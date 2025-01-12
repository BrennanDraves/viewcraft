import pytest
from django.db.models import QuerySet
from viewcraft import Component, ComponentConfig
from viewcraft.enums import HookMethod

class SimpleFilterComponent(Component):
    """A very simple component that just filters blog posts by status."""

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        filtered = queryset.filter(status='published')
        return filtered

class SimpleFilterConfig(ComponentConfig):
    def build_component(self, view):
        return SimpleFilterComponent(view)

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


# Test Components
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
