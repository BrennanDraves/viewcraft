from enum import Enum


class HookType(Enum):
    """Types of hooks that can be registered on view methods."""
    PRE = "pre"
    AROUND = "around"
    POST = "post"

class ViewMethod(Enum):
    """View methods that can be hooked into by components."""
    # Base View methods
    DISPATCH = "dispatch"
    HTTP_METHOD_NOT_ALLOWED = "http_method_not_allowed"
    OPTIONS = "options"

    # Template View methods
    GET_CONTEXT_DATA = "get_context_data"
    GET_TEMPLATE_NAMES = "get_template_names"
    RENDER_TO_RESPONSE = "render_to_response"

    # Display View methods
    GET_QUERYSET = "get_queryset"
    GET_OBJECT = "get_object"
    GET_CONTEXT_OBJECT_NAME = "get_context_object_name"

    # List View specific
    GET_ALLOW_EMPTY = "get_allow_empty"
    GET_PAGINATE_BY = "get_paginate_by"
    GET_PAGINATOR = "get_paginator"
    PAGINATE_QUERYSET = "paginate_queryset"

    # Form View methods
    GET_INITIAL = "get_initial"
    GET_FORM_CLASS = "get_form_class"
    GET_FORM = "get_form"
    GET_FORM_KWARGS = "get_form_kwargs"
    GET_PREFIX = "get_prefix"
    GET_SUCCESS_URL = "get_success_url"
    FORM_VALID = "form_valid"
    FORM_INVALID = "form_invalid"

    # Create/Update View methods
    GET_FIELDS = "get_fields"

    # Date-based View methods
    GET_DATE_FIELD = "get_date_field"
    GET_ALLOW_FUTURE = "get_allow_future"
    GET_DATE_LIST_PERIOD = "get_date_list_period"
    GET_YEAR = "get_year"
    GET_MONTH = "get_month"
    GET_DAY = "get_day"
    GET_WEEK = "get_week"
    GET_NEXT_YEAR = "get_next_year"
    GET_PREVIOUS_YEAR = "get_previous_year"
    GET_NEXT_MONTH = "get_next_month"
    GET_PREVIOUS_MONTH = "get_previous_month"
    GET_NEXT_DAY = "get_next_day"
    GET_PREVIOUS_DAY = "get_previous_day"
    GET_NEXT_WEEK = "get_next_week"
    GET_PREVIOUS_WEEK = "get_previous_week"

    # Auth View methods
    GET_USER = "get_user"
    GET_USER_KWARGS = "get_user_kwargs"

    # Response methods
    GET_REDIRECT_URL = "get_redirect_url"
    GET_REDIRECT_FIELD_NAME = "get_redirect_field_name"
