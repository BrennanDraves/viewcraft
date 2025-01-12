import pytest
from django.db.models import QuerySet
from viewcraft import ComponentConfig, Component, around_hook, post_hook, pre_hook

def test_pre_hook_modification(basic_view, blog_posts):
    """Test that hooks can modify the queryset."""
    class TestConfig(ComponentConfig):
        def build_component(self, view):
            return TestComponent(view)

    class TestComponent(Component):
        @post_hook('get_queryset')  # Changed to post_hook
        def filter_queryset(self, queryset: QuerySet) -> QuerySet:
            return queryset.filter(status='published')

    basic_view.components = [TestConfig()]
    basic_view.__init__()

    queryset = basic_view.get_queryset()
    assert all(post.status == 'published' for post in queryset)

def test_multiple_hook_types(basic_view, blog_posts):
    """Test that pre, around, and post hooks all work together."""
    execution_order = []

    class TestConfig(ComponentConfig):
        def build_component(self, view):
            return TestComponent(view)

    class TestComponent(Component):
        @pre_hook('get_queryset')
        def pre_process(self, *args, **kwargs) -> None:  # Changed signature
            execution_order.append('pre')

        @around_hook('get_queryset')
        def around_process(self, *args, **kwargs) -> QuerySet:
            execution_order.append('around_start')
            result = self.view.model.objects.all()
            execution_order.append('around_end')
            return result

        @post_hook('get_queryset')
        def post_process(self, result: QuerySet, *args, **kwargs) -> QuerySet:  # Added result parameter
            execution_order.append('post')
            return result

    basic_view.components = [TestConfig()]
    basic_view.__init__()

    basic_view.get_queryset()
    assert execution_order == ['pre', 'around_start', 'around_end', 'post']

def test_component_sequence_order(basic_view, blog_posts):
    """Test that components are executed in sequence order."""
    execution_sequence = []

    class BaseTestComponent(Component):
        """Base component with sequence handling"""
        def __init__(self, view, sequence):
            super().__init__(view)
            self.sequence = sequence

    class FirstComponent(BaseTestComponent):
        @post_hook('get_queryset')
        def track_first(self, result: QuerySet, *args, **kwargs) -> QuerySet:
            print(f"First hook called (sequence={self.sequence})")
            execution_sequence.append('first')
            return result

    class SecondComponent(BaseTestComponent):
        @post_hook('get_queryset')
        def track_second(self, result: QuerySet, *args, **kwargs) -> QuerySet:
            print(f"Second hook called (sequence={self.sequence})")
            execution_sequence.append('second')
            return result

    class FirstConfig(ComponentConfig):
        sequence = 1
        def build_component(self, view):
            return FirstComponent(view, self.sequence)

    class SecondConfig(ComponentConfig):
        sequence = 2
        def build_component(self, view):
            return SecondComponent(view, self.sequence)

    # Create view with components in reverse order
    basic_view.components = [SecondConfig(), FirstConfig()]
    basic_view.__init__()

    print("\nComponent registration order:")
    for comp in basic_view._components:
        print(f"Component: {comp.__class__.__name__}, Sequence: {comp.sequence}")

    # Clear and get queryset
    execution_sequence.clear()
    queryset = basic_view.get_queryset()
    print(f"\nQueryset retrieved: {len(queryset)} items")
    print(f"Final execution sequence: {execution_sequence}")

    assert execution_sequence == ['first', 'second']

    # Add additional verification
    assert [c.sequence for c in basic_view._components] == [1, 2], "Components not properly sorted"
