"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Django imports
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """ Collect exceptions from servers """

    help = 'Collect exceptions from servers'

    def handle(self, *args, **options):
        from error_monitor.functions import collect_exceptions_from_servers
        collect_exceptions_from_servers()
