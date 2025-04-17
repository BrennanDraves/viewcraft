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
    """Test basic search filtering with encoded query."""
    # Create a blog post with a specific title for testing
    test_title = "TEST_UNIQUE_TITLE"
    BlogPost.objects.create(
        title=test_title,
        slug="test-slug",
        body="Test body",
        status="published",
        author=user
    )

    # Test with encoded query format
    view = search_view_class()
    view.setup(rf.get(f'/?q=title:{test_title}'))
    queryset = view.get_queryset()

    assert queryset.count() == 1
    assert queryset.first().title == test_title


def test_search_form_in_context(search_view):
    """Test that search form is added to context."""
    context = search_view.get_context_data()

    assert 'search_form' in context
    assert hasattr(context['search_form'], 'fields')
    assert 'search_param_name' in context


def test_multiple_field_search(search_view_class, rf, blog_posts, user):
    """Test search with multiple fields in encoded format."""
    # Create a specific post for testing
    BlogPost.objects.create(
        title="Multiple Field Test",
        slug="multiple-field-test",
        body="Special test content",
        status="published",
        category="Test Category",
        author=user
    )

    # Search with multiple parameters in encoded format
    view = search_view_class()
    view.setup(rf.get('/?q=title:Multiple Field Test,status:published'))
    queryset = view.get_queryset()

    assert queryset.count() == 1
    post = queryset.first()
    assert post.title == "Multiple Field Test"
    assert post.status == "published"


def test_no_results(search_view_class, rf, blog_posts):
    """Test search with no matching results."""
    view = search_view_class()
    view.setup(rf.get('/?q=title:NonExistentTitle'))
    queryset = view.get_queryset()

    assert queryset.count() == 0


def test_empty_search(search_view_class, rf, blog_posts):
    """Test with empty search parameters."""
    total_count = BlogPost.objects.count()

    view = search_view_class()
    view.setup(rf.get('/?q='))
    queryset = view.get_queryset()

    # Should return all posts when search is empty
    assert queryset.count() == total_count


def test_malformed_query(search_view_class, rf, blog_posts):
    """Test handling of malformed query strings."""
    total_count = BlogPost.objects.count()

    # Test missing colon in parameter
    view = search_view_class()
    view.setup(rf.get('/?q=titleNoColon'))
    queryset = view.get_queryset()
    assert queryset.count() == total_count  # Should ignore malformed parts

    # Test with invalid field name
    view = search_view_class()
    view.setup(rf.get('/?q=invalid_field:value'))
    queryset = view.get_queryset()
    assert queryset.count() == total_count  # Should ignore invalid fields


def test_url_generation(search_view_class, rf):
    """Test generation of encoded search URLs."""
    view = search_view_class()
    view.setup(rf.get('/'))
    component = view._initialized_components[0]

    # Test URL generation with single parameter
    url = component.get_encoded_search_url({'title': 'Test'})
    assert 'q=title%3ATest' in url  # Check for encoded colon (%3A)

    # Test URL generation with multiple parameters
    url = component.get_encoded_search_url({'title': 'Test', 'status': 'published'})
    assert 'q=' in url
    assert 'title%3ATest' in url  # Check for encoded colon
    assert 'status%3Apublished' in url  # Check for encoded colon

    # Test URL generation with empty parameters
    url = component.get_encoded_search_url({})
    assert 'q=' not in url  # Should remove parameter entirely if empty


def test_form_data_from_encoded_query(search_view_class, rf):
    """Test that form is populated correctly from encoded query."""
    view = search_view_class()
    view.setup(rf.get('/?q=title:Test Title,status:published'))
    view.object_list = BlogPost.objects.all()

    form = view.get_context_data()['search_form']
    assert form.data.get('title') == 'Test Title'
    assert form.data.get('status') == 'published'
