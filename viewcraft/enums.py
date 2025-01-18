"""
Enumerations used throughout the viewcraft package.

Contains definitions for hook method types and other core enumerations used by
the component system.
"""

from enum import Enum


class HookMethod(str, Enum):
    """
    Enumeration of supported hook method types in viewcraft components.

    This enum defines the standard hook points available in the component system.
    Each value represents a method name that can be hooked into by components,
    with the hook types being 'pre_', 'process_', and 'post_' variants of these
    method names.

    Inherits from str to allow for direct string comparison and usage in method
    name construction.
    """
    # Setup hooks
    SETUP = "setup"
    GET_QUERYSET = "get_queryset"
    GET_CONTEXT_DATA = "get_context_data"
    GET_TEMPLATE_NAMES = "get_template_names"

    # HTTP method hooks
    GET = "get"
    POST = "post"

    # Form handling hooks (for FormView/CreateView etc.)
    GET_FORM = "get_form"
    GET_FORM_CLASS = "get_form_class"
    FORM_VALID = "form_valid"
    FORM_INVALID = "form_invalid"

    # Response hooks
    RENDER_TO_RESPONSE = "render_to_response"

    def __str__(self) -> str:
        return self.value
