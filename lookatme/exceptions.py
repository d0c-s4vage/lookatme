"""
Exceptions used within lookatme
"""

class IgnoredByContrib(Exception):
    """Raised when a contrib module's function chooses to ignore the function
    call.
    """
    pass
