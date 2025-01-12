from typing import TypeVar

from django.views import View

ViewT = TypeVar('ViewT', bound=View)
