"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Project imports
from .views import view_handled_exception, collect_exceptions, \
    get_exception_details, resolve_exception

# Django imports
from django.conf.urls import patterns, url


urlpatterns = patterns(  # IGNORE:invalid-name
    '',
    url(
        r'^view/(?P<exception_id>\d+)/$',
        view_handled_exception,
        name='view_handled_exception'
    ),
    url(
        r'^collect_exceptions/$',
        collect_exceptions,
        name='collect_exceptions'
    ),
    url(
        r'^get_exception_details/$',
        get_exception_details,
        name='get_exception_details'
    ),
    url(
        r'^resolve_exception/$',
        resolve_exception,
        name='resolve_exception'
    )
)
