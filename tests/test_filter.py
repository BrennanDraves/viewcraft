import pytest
from django.db.models import QuerySet
from viewcraft.components.filter import FilterConfig, FilterComponent

@pytest.fixture
def filter_view(basic_view_class, rf):
    basic_view_class.components = [
        FilterConfig(fields={
            'status': ['draft', 'published'],
            'category': ['Technology', 'Travel'],
            'author': ['user_1', 'user_2']
        })
    ]
    view = basic_view_class()
    return view

def test_basic_filtering(filter_view, rf, blog_posts):
    """Test basic single-field filtering"""
    filter_view.setup(rf.get('/?filter=status:published'))
    queryset = filter_view.get_queryset()

    assert all(post.status == 'published' for post in queryset)

def test_multiple_field_filtering(filter_view, rf, blog_posts):
    """Test filtering on multiple fields"""
    filter_view.setup(rf.get('/?filter=status:published,category:Technology'))
    queryset = filter_view.get_queryset()

    assert all(
        post.status == 'published' and post.category == 'Technology'
        for post in queryset
    )

def test_multiple_values(filter_view, rf, blog_posts):
    """Test filtering with multiple values for a field"""
    filter_view.setup(rf.get('/?filter=status:[published,draft]'))
    queryset = filter_view.get_queryset()

    assert all(post.status in ['published', 'draft'] for post in queryset)

def test_invalid_field(filter_view, rf, blog_posts):
    """Test that invalid fields are ignored"""
    filter_view.setup(rf.get('/?filter=invalid:value,status:published'))
    queryset = filter_view.get_queryset()

    assert all(post.status == 'published' for post in queryset)

def test_invalid_value(filter_view, rf, blog_posts):
    """Test handling of invalid filter values"""
    filter_view.setup(rf.get('/?filter=status:invalid'))
    queryset = filter_view.get_queryset()

    # Should return empty queryset when no valid matches
    assert queryset.count() == 0

def test_empty_filter(filter_view, rf, blog_posts):
    """Test with empty filter parameter"""
    filter_view.setup(rf.get('/?filter='))
    queryset = filter_view.get_queryset()

    # Should return unfiltered queryset
    assert queryset.count() == len(blog_posts)

def test_malformed_filter(filter_view, rf, blog_posts):
    """Test handling of malformed filter strings"""
    filter_view.setup(rf.get('/?filter=malformed'))
    queryset = filter_view.get_queryset()

    # Should ignore malformed filters
    assert queryset.count() == len(blog_posts)

def test_filter_caching(filter_view, rf, blog_posts):
    """Test that parsed filters are cached"""
    request = rf.get('/?filter=status:published')
    filter_view.setup(request)

    component = filter_view._initialized_components[0]

    # First call should parse
    filters1 = component._parse_filters()
    # Second call should use cached value
    filters2 = component._parse_filters()

    assert filters1 is filters2

def test_custom_param_name(basic_view_class, rf, blog_posts):
    """Test using a custom parameter name"""
    basic_view_class.components = [
        FilterConfig(
            fields={'status': ['published']},
            param_name='custom'
        )
    ]
    view = basic_view_class()
    view.setup(rf.get('/?custom=status:published'))

    queryset = view.get_queryset()
    assert all(post.status == 'published' for post in queryset)
