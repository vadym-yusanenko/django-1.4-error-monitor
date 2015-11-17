"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Django imports
from django.db.models import Model, TextField, CharField, \
    PositiveIntegerField, DateTimeField


class ProjectException(Model):
    """
    Table for storing caught exceptions.
    """

    path = CharField(max_length=255)
    contents = TextField()
    title = TextField(null=True, blank=True)
    date = DateTimeField(auto_now_add=True)
    count = PositiveIntegerField()
    hash = CharField(max_length=100)

    def __unicode__(self):
        return self.title or 'No title'


class CollectedProjectException(Model):
    """
    Table for storing caught exceptions.
    """

    path = CharField(max_length=255)
    contents = TextField()
    title = TextField(null=True, blank=True)
    date = DateTimeField(auto_now_add=True)
    count = PositiveIntegerField()
    hash = CharField(max_length=100)
    servers = TextField()
    server_count = PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.title or 'No title'
