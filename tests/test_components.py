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
