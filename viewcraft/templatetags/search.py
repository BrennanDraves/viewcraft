"""
Template tags for the search component.

Provides template filters and tags for rendering the search form and working
with search parameters in templates.
"""
from typing import Optional

from django import template
from django.forms import BoundField, Form

register = template.Library()


@register.filter
def get_field(form: Form, field_name: str) -> Optional[BoundField]:
    """
    Get a field from a form by name.

    Args:
        form: The form instance
        field_name: The name of the field to retrieve

    Returns:
        The field bound to the form, or None if not found
    """
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def endswith(value: str, suffix: str) -> bool:
    """
    Check if a string ends with a given suffix.

    Args:
        value: The string to check
        suffix: The suffix to check for

    Returns:
        bool: True if the string ends with the suffix, False otherwise
    """
    return value.endswith(suffix)


@register.filter
def split(value: str, delimiter: str) -> list:
    """
    Split a string by a delimiter.

    Args:
        value: The string to split
        delimiter: The delimiter to split on

    Returns:
        list: The parts of the string after splitting
    """
    return value.split(delimiter)


@register.filter
def get_item(dictionary: dict, key: str) -> Optional[str]:
    """
    Get an item from a dictionary by key.

    Args:
        dictionary: The dictionary to get the item from
        key: The key to look up

    Returns:
        The value for the key, or None if not found
    """
    return dictionary.get(key)


@register.filter
def add(value: str, arg: str) -> str:
    """
    Concatenate two strings.

    Args:
        value: The first string
        arg: The string to append

    Returns:
        str: The concatenated string
    """
    return value + arg
