"""
Type definitions for viewcraft.

Defines core type variables and annotations used throughout the package
to provide consistent type hinting and improve static type checking.
"""

from typing import TypeVar

from django.views import View

ViewT = TypeVar('ViewT', bound=View)
"""
TypeVar representing a Django View class or subclass.

Used for maintaining type safety when working with view components
and mixins that can be applied to any Django view class.
"""
