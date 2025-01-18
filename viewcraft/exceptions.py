"""
Custom exceptions for the viewcraft package.

Defines a hierarchy of exceptions used throughout viewcraft to provide
specific error information and maintain consistent error handling.
"""

class ViewcraftError(Exception):
    """
    Base exception class for all viewcraft-specific errors.

    All other exceptions in the viewcraft package inherit from this class,
    allowing for catch-all error handling of viewcraft-specific issues.
    """
    pass

class ComponentError(ViewcraftError):
    """
    Exception raised for errors during component operations.

    Raised when there is an error in the configuration or execution of
    a component, such as invalid initialization parameters or runtime failures.
    """
    pass

class HookError(ComponentError):
    """
    Exception raised for errors during hook execution.

    Raised when a hook method fails to execute properly, such as when a hook
    is incorrectly defined or encounters an error during execution.
    """
    pass

class ConfigurationError(ViewcraftError):
    """
    Exception raised for invalid component configurations.

    Raised when component configuration is invalid, such as missing required
    parameters or incompatible configuration options.
    """
    pass
