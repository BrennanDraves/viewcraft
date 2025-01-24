import pytest
from django.core.paginator import InvalidPage
from django.db.models import QuerySet

from viewcraft.components.pagination import (
    PaginationConfig,
    PaginationComponent,
    InvalidPageError,
    ConfigurationError
)

@pytest.fixture
def paginated_view(basic_view_class, rf):
    """View with pagination component."""
    basic_view_class.components = [PaginationConfig(per_page=2)]
    view = basic_view_class()
    view.setup(rf.get('/'))
    return view

def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ConfigurationError):
        PaginationConfig(per_page=0)

    with pytest.raises(ConfigurationError):
        PaginationConfig(max_pages=0)

    with pytest.raises(ConfigurationError):
        PaginationConfig(visible_pages=0)

def test_basic_pagination(paginated_view, blog_posts):
    """Test basic pagination functionality."""
    queryset = paginated_view.get_queryset()
    assert len(queryset) == 2  # per_page=2

    context = paginated_view.get_context_data(object_list=queryset)
    page_obj = context['page_obj']

    assert page_obj['number'] == 1
    assert page_obj['has_next']
    assert not page_obj['has_previous']
    assert page_obj['total_count'] == 5  # from blog_posts fixture

def test_invalid_page(basic_view_class, rf, blog_posts):
    """Test handling of invalid page numbers."""
    basic_view_class.components = [PaginationConfig()]
    view = basic_view_class()

    # Test negative page
    view.setup(rf.get('/?page=-1'))
    with pytest.raises(InvalidPageError):
        view.get_queryset()

    # Test out-of-range page
    view.setup(rf.get('/?page=999'))
    with pytest.raises(InvalidPageError):
        view.get_queryset()

def test_page_range_calculation(basic_view_class, rf, blog_posts):
    """Test visible page range calculation."""
    config = PaginationConfig(per_page=1, visible_pages=3)  # 5 total pages, show 3
    basic_view_class.components = [config]
    view = basic_view_class()

    # Test start of range
    view.setup(rf.get('/?page=1'))
    context = view.get_context_data(object_list=view.get_queryset())
    assert context['page_obj']['page_range'] == [1, 2, 3]

    # Test middle of range
    view.setup(rf.get('/?page=3'))
    context = view.get_context_data(object_list=view.get_queryset())
    assert context['page_obj']['page_range'] == [2, 3, 4]

    # Test end of range
    view.setup(rf.get('/?page=5'))
    context = view.get_context_data(object_list=view.get_queryset())
    assert context['page_obj']['page_range'] == [3, 4, 5]

def test_url_generation(basic_view_class, rf, blog_posts):
    """Test pagination URL generation."""
    view = basic_view_class()
    view.components = [PaginationConfig(per_page=1)]
    view.setup(rf.get('/test/?sort=name'))

    context = view.get_context_data(object_list=view.get_queryset())
    urls = context['page_obj']['page_urls']

    # Check URL structure and parameter handling
    assert 'page=2' in urls['next']
    assert 'sort=name' in urls['next']  # Preserves existing params
    assert urls['previous'] is None  # On first page
    assert 'page=1' in urls['first']
    assert isinstance(urls['pages'], dict)

def test_max_pages_limit(basic_view_class, rf, blog_posts):
    """Test max_pages configuration."""
    config = PaginationConfig(per_page=1, max_pages=3)
    basic_view_class.components = [config]
    view = basic_view_class()
    view.setup(rf.get('/'))

    context = view.get_context_data(object_list=view.get_queryset())
    assert context['page_obj']['total_pages'] == 3  # Limited by max_pages

    # Test page beyond max_pages
    view.setup(rf.get('/?page=4'))
    with pytest.raises(InvalidPageError):
        view.get_queryset()
