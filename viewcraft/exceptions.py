class ViewcraftError(Exception):
    """Base exception for all viewcraft errors"""
    pass

class ComponentError(ViewcraftError):
    """Raised when there's an error in component configuration or execution"""
    pass

class HookError(ComponentError):
    """Raised when there's an error in hook execution"""
    pass

class ConfigurationError(ViewcraftError):
    """Raised for invalid component configurations"""
    pass
