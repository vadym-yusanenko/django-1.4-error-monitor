"""
Copyright: Vadim Yusanenko, Konstantin Volkov, Denis Motsak
License: BSD
"""

# Project imports
from .models import ProjectException, CollectedProjectException

# Django imports
from django.contrib import admin
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response, HttpResponseRedirect


def exception_view_link(exception_object):
    """
    Generate HTML with exception on click.
    """
    return (
        '<a target="_blank" href="%s">Details</a>'
        %
        reverse(
            "admin:exception_content_views",
            kwargs={'object_id': str(exception_object.id)}
        )
    )

exception_view_link.short_description = 'View exception'
exception_view_link.allow_tags = True


class ProjectExceptionAdmin(admin.ModelAdmin):
    """
    Link to exception in admin panel.
    """
    list_display = ('count', 'title', 'path', 'date', exception_view_link)
    search_fields = ('title', 'path')
    ordering = ('-date',)

    def queryset(self, request):
        query_set = super(ProjectExceptionAdmin, self).queryset(request)
        return query_set.only(
            "id", "title", "path", "date", "count"
        )

    @staticmethod
    def exception_content_views(
        request, object_id, extra_context=None  # IGNORE:unused-argument
    ):
        """
        Render HTML with exception.
        """
        exception_object = get_object_or_404(ProjectException, id=object_id)
        return render_to_response(
            'view_handled_exception.html',
            {'contents': exception_object.contents}
        )

    def get_urls(self):
        urls = super(ProjectExceptionAdmin, self).get_urls()
        additional_urls = patterns(
            '',
            url(
                r'^(?P<object_id>.+)/view/$',
                self.admin_site.admin_view(self.exception_content_views),
                name="exception_content_views"
            )
        )
        return additional_urls + urls


def collected_exception_view_link(exception_object):
    """
    Generate HTML with exception on click.
    """
    return (
        '<a target="_blank" href="%s">Details</a>'
        %
        reverse(
            "admin:collected_exception_content_views",
            kwargs={'object_id': str(exception_object.id)}
        )
    )

collected_exception_view_link.short_description = 'View exception'
collected_exception_view_link.allow_tags = True


def exception_resolve_link(exception_object):
    """
    Generate HTML with exception on click.
    """
    return (
        '<a href="%s">Resolve</a>'
        %
        reverse(
            "admin:collected_exception_resolve",
            kwargs={'object_id': str(exception_object.id)}
        )
    )

exception_resolve_link.short_description = 'Resolve exception'
exception_resolve_link.allow_tags = True


class CollectedProjectExceptionAdmin(admin.ModelAdmin):
    """
    Link to exception in admin panel.
    """
    list_display = (
        'count',
        'title',
        'path',
        'server_count',
        collected_exception_view_link,
        exception_resolve_link
    )
    search_fields = ('title', 'path')
    ordering = ('-date',)

    def queryset(self, request):
        query_set = super(CollectedProjectExceptionAdmin, self).queryset(request)
        return query_set.only(
            "id", "title", "path", "server_count", "count"
        )

    @staticmethod
    def collected_exception_content_views(
        request, object_id, extra_context=None  # IGNORE:unused-argument
    ):
        """
        Render HTML with exception.
        """
        exception_object = get_object_or_404(CollectedProjectException, id=object_id)
        return render_to_response(
            'view_handled_exception.html',
            {'contents': exception_object.contents}
        )

    @staticmethod
    def collected_exception_resolve(
        request, object_id, extra_context=None  # IGNORE:unused-argument
    ):
        """
        Delete exceptions.
        """
        from .functions import resolve_exceptions_from_servers
        exception_object = get_object_or_404(CollectedProjectException, id=object_id)
        resolve_exceptions_from_servers(exception_object)
        exception_object.delete()

        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    def get_urls(self):
        urls = super(CollectedProjectExceptionAdmin, self).get_urls()

        additional_urls = patterns(
            '',
            url(
                r'^(?P<object_id>.+)/collected_view/$',
                self.admin_site.admin_view(self.collected_exception_content_views),
                name="collected_exception_content_views"
            ),
            url(
                r'^(?P<object_id>.+)/collected_resolve/$',
                self.admin_site.admin_view(self.collected_exception_resolve),
                name="collected_exception_resolve"
            ),
        )

        return additional_urls + urls


admin.site.register(ProjectException, ProjectExceptionAdmin)
admin.site.register(CollectedProjectException, CollectedProjectExceptionAdmin)
