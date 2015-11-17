"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Project related imports
from .functions import record_exception


class ExceptionMiddleware(object):  # IGNORE:too-few-public-methods
    """
    Middleware that saves exception for later investigation.
    """

    def process_exception(self, request, exception):  # IGNORE:no-self-use
        """
        Get exception and save it in database.
        """

        record_exception(exception=exception, request=request)
