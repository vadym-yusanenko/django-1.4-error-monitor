"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Standard imports
from re import search, I, findall
from warnings import warn
from hashlib import md5
from datetime import datetime, timedelta
from sys import exc_info
from traceback import print_exc
from urllib2 import urlopen, Request
from urllib import urlencode
from json import loads

# Core Django imports
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import F
from django.db import connections

# Third-party app imports
from pytz import utc
from psycopg2 import InterfaceError

# Project related imports
from .models import ProjectException, CollectedProjectException
from .views import CustomExceptionReporter


EXCEPTION_TITLE_WORDS_TO_NOTIFY = getattr(
    settings, 'ERROR_MONITOR_EXCEPTION_TITLE_WORDS_TO_NOTIFY', ()
)
EXCEPTION_RECIPIENTS = getattr(
    settings, 'ERROR_MONITOR_EXCEPTION_RECIPIENTS', ()
)
ERROR_MONITOR_EXCEPTION_LIFETIME = getattr(
    settings, 'ERROR_MONITOR_EXCEPTION_LIFETIME', 90
)

if not EXCEPTION_TITLE_WORDS_TO_NOTIFY:
    warn(
        'Please specify '
        'ERROR_MONITOR_EXCEPTION_TITLE_WORDS_TO_NOTIFY '
        'in settings.'
    )

if not EXCEPTION_RECIPIENTS:
    warn('Please specify ERROR_MONITOR_EXCEPTION_RECIPIENTS in settings.')


def record_exception(exception, title=None, title_prefix=None, request=None):
    """
    Record caught exception in database.
    If connection is broken - mark it as unavailable - so it will be reset.
    Send emails if it is identified as critical.
    Print exception in the end.
    """
    current_exception = exc_info()
    exception_data = CustomExceptionReporter(  # IGNORE:star-args
        request, *current_exception
    )
    html_content = exception_data.get_traceback_html()
    occurrences = findall(
        '<th>Exception Location:</th>\n'
        '[ ]+<td>(.*, line [0-9]+)</td>',
        html_content
    )
    location_hash = (
        md5(occurrences[0]).hexdigest() if len(occurrences) == 1 else ''
    )

    if not title:
        title = str(exception)

    if title_prefix:
        title = title_prefix + title

    path = request.path if request else 'N/A'

    notify_about_exception(title)

    print_exc()

    try:
        if ProjectException.objects.filter(
            hash=location_hash, title=title, path=path
        ).update(
            count=F('count') + 1,
            contents=html_content,
            date=datetime.utcnow().replace(tzinfo=utc)
        ) == 0:
            ProjectException.objects.create(
                path=path,
                contents=html_content,
                title=title,
                hash=location_hash,
                count=1
            )
        ProjectException.objects.filter(
            date__lte=datetime.utcnow() - timedelta(
                days=ERROR_MONITOR_EXCEPTION_LIFETIME
            )
        ).delete()
    except InterfaceError, database_exception:
        if str(database_exception).lower() == 'connection already closed':
            print 'Closing broken connections...'
            for connection in connections:
                connections[connection].connection = None
        raise database_exception


def notify_about_exception(exception_title):
    """
    If exception is identified as critical - send email to recipients.
    """
    if EXCEPTION_TITLE_WORDS_TO_NOTIFY and EXCEPTION_RECIPIENTS:
        pattern = r'|'.join(EXCEPTION_TITLE_WORDS_TO_NOTIFY)
        search_result = search(pattern, exception_title, I)

        if search_result is not None:
            message_content = (
                "<p>%(body)s</p><p>Server: "
                "<a href='%(protocol)s://%(domain)s'>%(domain)s</a></p>" % (
                    {
                        'body': exception_title,
                        'protocol': settings.SERVER_PROTOCOL,
                        'domain': settings.CURRENT_SERVER_DOMAIN
                    }
                )
            )
            message = EmailMessage(
                "Error Monitor notification",
                message_content,
                settings.EMAIL_HOST_USER,
                EXCEPTION_RECIPIENTS
            )
            message.content_subtype = 'html'
            message.send(fail_silently=True)


def collect_exceptions_from_servers():
    """ Collect exceptions from remote servers. """

    target_servers_list = getattr(settings, 'ERROR_MONITOR_EXCEPTION_SERVERS_LIST', [])

    CollectedProjectException.objects.all().delete()

    hash_list = []
    target_server = {}

    for server in target_servers_list:
        print "=> Collecting exceptions from %s" % server
        response_dict = urlopen(
            Request(
                url=(
                    '%s/error_monitor/collect_exceptions/'
                    %
                    server
                ),
                data=urlencode(
                    {'secret_key': settings.ERROR_MONITOR_SECRET_KEY},
                    doseq=True
                )
            ),
            timeout=20
        ).read()

        errors_list = loads(response_dict)

        expected_parameters = ["path", "title", "count", "hash"]
        path_index = []

        for value in expected_parameters:
            path_index.append(errors_list[0].index(value))

        for error in errors_list[1:]:
            try:
                if CollectedProjectException.objects.filter(
                    hash=error[path_index[3]], title=error[path_index[1]], path=error[path_index[0]]
                ).update(
                    count=F('count') + error[path_index[2]],
                    date=datetime.utcnow().replace(tzinfo=utc),
                    server_count=F('server_count') + 1,
                ) == 0:
                    CollectedProjectException.objects.create(
                        path=error[path_index[0]],
                        title=error[path_index[1]],
                        hash=error[path_index[3]],
                        count=error[path_index[2]],
                        server_count=1,
                        servers=server
                    )
                else:
                    CollectedProjectException.objects.filter(
                        hash=error[path_index[3]],
                        title=error[path_index[1]],
                        path=error[path_index[0]]
                    ).update(
                        servers='%s, %s' % (
                            CollectedProjectException.objects.filter(
                                hash=error[path_index[3]],
                                title=error[path_index[1]],
                                path=error[path_index[0]]
                            )[0].servers,
                        server
                        )
                    )

                if not error[path_index[3]] in hash_list:
                    if not server in target_server:
                        target_server[server] = []

                    target_server[server].append(error[path_index[3]])
                    hash_list.append(error[path_index[3]])

            except InterfaceError, database_exception:
                if str(database_exception).lower() == 'connection already closed':
                    print 'Closing broken connections...'
                    for connection in connections:
                        connections[connection].connection = None
                raise database_exception

    for server, hashes_list in target_server.items():
        print "=> Getting exception details from %s" % server
        response_dict = urlopen(
            Request(
                url=(
                    '%s/error_monitor/get_exception_details/'
                    %
                    server
                ),
                data=urlencode(
                    {
                        'secret_key': settings.ERROR_MONITOR_SECRET_KEY,
                        'hashes': ' '.join(hashes_list)
                    },
                    doseq=True
                )
            ),
            timeout=20
        ).read()

        errors_list = loads(response_dict)

        expected_parameters = ["contents", "hash"]
        path_index = []

        for value in expected_parameters:
            path_index.append(errors_list[0].index(value))

        for error in errors_list[1:]:
            CollectedProjectException.objects.filter(
                hash=error[path_index[1]]
            ).update(
                contents=error[path_index[0]]
            )


def resolve_exceptions_from_servers(exception_object):
    """ Request details on specific exception from one of the aware servers. """
    for server in exception_object.servers.split(','):
        urlopen(
            Request(
                url=(
                    '%s/error_monitor/resolve_exception/'
                    %
                    server
                ),
                data=urlencode(
                    {
                        'secret_key': settings.ERROR_MONITOR_SECRET_KEY,
                        'hash': exception_object.hash
                    },
                    doseq=True
                )
            ),
            timeout=20
        ).read()
