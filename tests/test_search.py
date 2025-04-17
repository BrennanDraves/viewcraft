import pytest
from django.views.generic import ListView
from viewcraft import ComponentMixin
from viewcraft.components.search import BasicSearchConfig
from demo_app.models import BlogPost
from tests.factories import UserFactory


@pytest.fixture
def user():
    """Create a test user for authors."""
    return UserFactory()


@pytest.fixture
def search_view_class():
    """View class with basic search component."""
    class TestSearchView(ComponentMixin, ListView):
        model = BlogPost
        template_name = 'blog/list.html'
        components = [BasicSearchConfig(model=BlogPost)]

    return TestSearchView


@pytest.fixture
def search_view(search_view_class, rf, blog_posts):
    """Instantiated view with search component."""
    view = search_view_class()
    request = rf.get('/')
    view.setup(request)
    view.object_list = blog_posts  # Set object_list for get_context_data
    return view


def test_search_config_validation():
    """Test search configuration validation."""
    # Should work with model
    config = BasicSearchConfig(model=BlogPost)
    assert len(config.fields) > 0

    # Should work with explicit fields
    config = BasicSearchConfig(fields=['title', 'body'])
    assert config.fields == ['title', 'body']

    # Should fail with no model and no fields
    with pytest.raises(Exception):
        BasicSearchConfig()


def test_basic_search_filtering(search_view_class, rf, blog_posts, user):
    """Test basic search filtering."""
    # Create a blog post with a specific title for testing
    test_title = "TEST_UNIQUE_TITLE"
    BlogPost.objects.create(
        title=test_title,
        slug="test-slug",
        body="Test body",
        status="published",
        author=user  # Add author to fix IntegrityError
    )

    # Test exact match on title
    view = search_view_class()
    view.setup(rf.get(f'/?title={test_title}'))
    queryset = view.get_queryset()

    assert queryset.count() == 1
    assert queryset.first().title == test_title


def test_search_form_in_context(search_view):
    """Test that search form is added to context."""
    context = search_view.get_context_data()

    assert 'search_form' in context
    assert hasattr(context['search_form'], 'fields')


def test_multiple_field_search(search_view_class, rf, blog_posts, user):
    """Test search with multiple fields."""
    # Create a specific post for testing
    BlogPost.objects.create(
        title="Multiple Field Test",
        slug="multiple-field-test",
        body="Special test content",
        status="published",
        category="Test Category",
        author=user  # Add author to fix IntegrityError
    )

    # Search with multiple parameters
    view = search_view_class()
    view.setup(rf.get('/?title=Multiple Field Test&status=published'))
    queryset = view.get_queryset()

    assert queryset.count() == 1
    post = queryset.first()
    assert post.title == "Multiple Field Test"
    assert post.status == "published"


def test_no_results(search_view_class, rf, blog_posts):
    """Test search with no matching results."""
    view = search_view_class()
    view.setup(rf.get('/?title=NonExistentTitle'))
    queryset = view.get_queryset()

    assert queryset.count() == 0


def test_empty_search(search_view_class, rf, blog_posts):
    """Test with empty search parameters."""
    total_count = BlogPost.objects.count()

    view = search_view_class()
    view.setup(rf.get('/?title='))
    queryset = view.get_queryset()

    # Should return all posts when search is empty
    assert queryset.count() == total_count
