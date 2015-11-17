"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Project imports
from .models import ProjectException

# Django imports
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.contrib.admin.views.decorators import staff_member_required
from django.views.debug import ExceptionReporter
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Standard imports
from json import dumps


SIMPLIFIED_TEMPLATE = loader.get_template('simplified_exception.html')
VARIABLE_LENGTH = getattr(settings, 'ERROR_MONITOR_EXCEPTION_VARIABLE_LENGTH', 2000)


@staff_member_required
def view_handled_exception(request, exception_id):
    """
    Return HTML contents of specified exception.
    """

    return render_to_response(
        'view_handled_exception.html',
        {
            "content": ProjectException.objects.filter(
                id=exception_id
            ).values_list('contents', flat=True)[0]
        },
        context_instance=RequestContext(request)
    )


@csrf_exempt
def collect_exceptions(request):
    """
    Collect and send exceptions collected via error_monitor package.
    """
    if (
        'secret_key' not in request.POST
    ) or (
        settings.ERROR_MONITOR_SECRET_KEY != request.POST['secret_key']
    ):
        return HttpResponse('Access denied')

    keys = ['path', 'title', 'count', 'hash']

    all_exceptions = ProjectException.objects.all().values_list(*keys)
    return HttpResponse(content=dumps([keys] + list(all_exceptions)), mimetype='application/json')


@csrf_exempt
def get_exception_details(request):
    """
    Send exception details based on received exception hashes.
    """
    if (
        'secret_key' not in request.POST
    ) or (
        settings.ERROR_MONITOR_SECRET_KEY != request.POST['secret_key']
    ):
        return HttpResponse('Access denied')

    keys = ['hash', 'contents']

    exception_details = ProjectException.objects.filter(
        hash__in=request.POST['hashes'].split(' ')
    ).values_list(*keys)
    return HttpResponse(
        content=dumps([keys] + list(exception_details)), mimetype='application/json'
    )


@csrf_exempt
def resolve_exception(request):
    """
    Delete exception occurences from error_monitor to check whether it will appear again.
    """
    if (
        'secret_key' not in request.POST
    ) or (
        settings.ERROR_MONITOR_SECRET_KEY != request.POST['secret_key']
    ):
        return HttpResponse('Access denied')

    ProjectException.objects.filter(hash=request.POST['hash']).delete()
    return HttpResponse('Done')


class CustomExceptionReporter(ExceptionReporter):
    """
    Customized ExceptionReporter class to use SIMPLIFIED_500_TEMPLATE.
    """

    def get_traceback_html(self):
        """Return HTML version of debug 500 HTTP error page."""

        return SIMPLIFIED_TEMPLATE.render(
            Context(
                dict({"VAR_LENGTH": VARIABLE_LENGTH}, **self.get_traceback_data())
            )
        )
