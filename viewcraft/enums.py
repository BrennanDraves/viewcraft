from enum import Enum


class HookMethod(str, Enum):
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
