import pytest
from django.http import HttpRequest
from django.test import RequestFactory
from viewcraft import Component
from viewcraft.utils import modify_query_params, URLMixin

# Fixtures
@pytest.fixture
def rf():
    return RequestFactory()

@pytest.fixture
def request_with_params(rf):
    """Request with some existing query parameters"""
    return rf.get('/test/', {'page': '2', 'sort': 'name', 'filter': 'active'})

@pytest.fixture
def empty_request(rf):
    """Request with no query parameters"""
    return rf.get('/test/')

# Test modify_query_params utility function
def test_add_new_param(empty_request):
    """Test adding a new parameter to a URL with no existing params"""
    url = modify_query_params(empty_request, {'page': '1'})
    assert url == '/test/?page=1'

def test_update_existing_param(request_with_params):
    """Test updating an existing parameter"""
    url = modify_query_params(request_with_params, {'page': '3'})
    assert 'page=3' in url
    assert 'sort=name' in url
    assert 'filter=active' in url

def test_remove_param(request_with_params):
    """Test removing a parameter by setting it to None"""
    url = modify_query_params(request_with_params, {'page': None})
    assert 'page=' not in url
    assert 'sort=name' in url
    assert 'filter=active' in url

def test_multiple_param_updates(request_with_params):
    """Test updating multiple parameters at once"""
    url = modify_query_params(request_with_params, {
        'page': '5',
        'sort': None,
        'new': 'value'
    })
    assert 'page=5' in url
    assert 'sort=' not in url
    assert 'filter=active' in url
    assert 'new=value' in url

def test_special_characters(empty_request):
    """Test handling of special characters in parameter values"""
    url = modify_query_params(empty_request, {'search': 'hello world & more'})
    assert url == '/test/?search=hello+world+%26+more'

def test_multiple_values_same_param(rf):
    """Test handling request with multiple values for same parameter - should use last value"""
    request = rf.get('/test/?tag=python&tag=django')

    # Should keep the last value (django) when not explicitly modified
    url = modify_query_params(request, {'page': '1'})
    assert 'tag=django' in url
    assert 'tag=python' not in url
    assert 'page=1' in url

    # Should be able to override multiple values with a single new value
    url = modify_query_params(request, {'tag': 'newvalue', 'page': '1'})
    assert 'tag=newvalue' in url
    assert 'page=1' in url

def test_empty_result(request_with_params):
    """Test removing all parameters"""
    url = modify_query_params(request_with_params, {
        'page': None,
        'sort': None,
        'filter': None
    })
    assert url == '/test/'

def test_boolean_params(empty_request):
    """Test handling boolean parameter values"""
    url = modify_query_params(empty_request, {'active': True, 'deleted': False})
    assert 'active=True' in url
    assert 'deleted=False' in url

def test_numeric_params(empty_request):
    """Test handling numeric parameter values"""
    url = modify_query_params(empty_request, {'page': 1, 'per_page': 50})
    assert 'page=1' in url
    assert 'per_page=50' in url

# Test URLMixin
class DummyView:
    def __init__(self, request):
        self.request = request

class SampleComponent(Component, URLMixin):
    pass

@pytest.fixture
def url_component(request_with_params):
    view = DummyView(request_with_params)
    component = SampleComponent(view)
    return component

def test_mixin_get_url_with_params(url_component):
    """Test the mixin's get_url_with_params method"""
    url = url_component.get_url_with_params({'page': '10'})
    assert 'page=10' in url
    assert 'sort=name' in url
    assert 'filter=active' in url

def test_mixin_remove_param(url_component):
    """Test removing a parameter using the mixin"""
    url = url_component.get_url_with_params({'sort': None})
    assert 'page=2' in url
    assert 'sort=' not in url
    assert 'filter=active' in url

def test_mixin_with_complex_updates(url_component):
    """Test mixin with multiple parameter updates"""
    url = url_component.get_url_with_params({
        'page': '1',
        'sort': None,
        'filter': 'inactive',
        'search': 'test'
    })
    assert 'page=1' in url
    assert 'sort=' not in url
    assert 'filter=inactive' in url
    assert 'search=test' in url

# Edge cases and error handling
def test_none_params(empty_request):
    """Test handling when all new params are None"""
    url = modify_query_params(empty_request, {'page': None, 'sort': None})
    assert url == '/test/'

def test_empty_params_dict(request_with_params):
    """Test handling empty params dictionary"""
    url = modify_query_params(request_with_params, {})
    assert url == request_with_params.get_full_path()

def test_invalid_param_types(empty_request):
    """Test handling of invalid parameter types"""
    from urllib.parse import unquote

    url = modify_query_params(empty_request, {
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'none': None
    })

    # Decode URL before checking content
    decoded_url = unquote(url)
    assert 'dict=' in decoded_url
    assert 'list=' in decoded_url
    assert 'none=' not in decoded_url

    # Verify the values are being converted to strings somehow
    # (exact format isn't important, just that they're handled)
    assert any(key in decoded_url for key in ['key', 'value'])
    assert any(str(num) in decoded_url for num in [1, 2, 3])
