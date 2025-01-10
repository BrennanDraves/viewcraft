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
