"""Base class for viewcraft components."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from viewcraft import ViewT


class BaseComponent:
    """Base class for view components."""

    def __init__(self, view: "ViewT") -> None:
        """Initialize the component."""
        self.view = view
