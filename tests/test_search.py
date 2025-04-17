import pytest
import base64
import json
from urllib.parse import quote
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
def encoded_search_view_class():
    """View class with base64 encoded search component."""
    class TestEncodedSearchView(ComponentMixin, ListView):
        model = BlogPost
        template_name = 'blog/list.html'
        components = [BasicSearchConfig(model=BlogPost)]

    return TestEncodedSearchView


def test_base64_encoded_search(encoded_search_view_class, rf, blog_posts, user):
    """Test search with base64 encoded parameters."""
    # Create a blog post with a specific title for testing
    test_title = "TEST_UNIQUE_TITLE"
    BlogPost.objects.create(
        title=test_title,
        slug="test-slug",
        body="Test body",
        status="published",
        author=user
    )

    # Create base64 encoded search params
    search_params = {"title": test_title}
    json_params = json.dumps(search_params)
    # URL-safe base64 encoding
    encoded_params = base64.urlsafe_b64encode(json_params.encode('utf-8')).decode('utf-8')

    # Test with encoded query format
    view = encoded_search_view_class()
    view.setup(rf.get(f'/?q={encoded_params}'))
    queryset = view.get_queryset()

    assert queryset.count() == 1
    assert queryset.first().title == test_title


def test_malformed_base64_query(encoded_search_view_class, rf, blog_posts):
    """Test handling of malformed base64 encoded queries."""
    total_count = BlogPost.objects.count()

    # Test with invalid base64 string
    view = encoded_search_view_class()
    view.setup(rf.get('/?q=not-valid-base64!'))
    queryset = view.get_queryset()

    # Should return all posts when query can't be decoded
    assert queryset.count() == total_count

    # Test with valid base64 but invalid JSON
    invalid_json = base64.urlsafe_b64encode(b'not valid json').decode('utf-8')
    view = encoded_search_view_class()
    view.setup(rf.get(f'/?q={invalid_json}'))
    queryset = view.get_queryset()

    # Should handle invalid JSON gracefully
    assert queryset.count() == total_count


def test_url_generation_with_base64(encoded_search_view_class, rf):
    """Test generation of base64 encoded search URLs."""
    view = encoded_search_view_class()
    view.setup(rf.get('/'))
    component = view._initialized_components[0]

    # Test URL generation with single parameter
    url = component.get_encoded_search_url({'title': 'Test'})

    # URL should contain a base64 parameter
    assert 'q=' in url

    # Extract and decode the parameter
    param_value = url.split('q=')[1]
    # URL decode the parameter before decoding base64
    param_value = param_value.replace('%3D', '=')
    decoded = json.loads(base64.urlsafe_b64decode(param_value).decode('utf-8'))
    assert decoded == {'title': 'Test'}

    # Test URL generation with multiple parameters
    url = component.get_encoded_search_url({'title': 'Test', 'status': 'published'})
    param_value = url.split('q=')[1]
    # URL decode the parameter before decoding base64
    param_value = param_value.replace('%3D', '=')
    decoded = json.loads(base64.urlsafe_b64decode(param_value).decode('utf-8'))
    assert decoded == {'title': 'Test', 'status': 'published'}

    # Test URL generation with empty parameters
    url = component.get_encoded_search_url({})
    assert 'q=' not in url  # Should remove parameter entirely if empty


def test_form_data_from_base64_query(encoded_search_view_class, rf):
    """Test that form is populated correctly from base64 encoded query."""
    # Create base64 encoded search params
    search_params = {"title": "Test Title", "status": "published"}
    json_params = json.dumps(search_params)
    encoded_params = base64.urlsafe_b64encode(json_params.encode('utf-8')).decode('utf-8')

    view = encoded_search_view_class()
    view.setup(rf.get(f'/?q={encoded_params}'))
    view.object_list = BlogPost.objects.all()

    form = view.get_context_data()['search_form']
    assert form.data.get('title') == 'Test Title'
    assert form.data.get('status') == 'published'
