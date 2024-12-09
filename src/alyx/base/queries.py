import sys
from django.conf import settings
from django.db import connection
from django.utils import termcolors, timezone

from django.db.models import QuerySet, Manager


class QueryPrintingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        if settings.DEBUG:
            self.start = 0

    def __call__(self, request):
        response = self.get_response(request)

        if settings.DEBUG and "runserver" in sys.argv and self.start is not None:
            red = termcolors.make_style(opts=("bold",), fg="red")
            yellow = termcolors.make_style(opts=("bold",), fg="yellow")

            count = len(connection.queries) - self.start
            output = "# queries: %s" % count
            output = output.ljust(18)

            # add some colour
            if count > 100:
                output = red(output)
            elif count > 10:
                output = yellow(output)

            # runserver just prints its output to sys.stderr, so follow suite
            sys.stderr.write(output)

            # for q in connection.queries:
            #     print(q['sql'])

        return response


class BaseQuerySet(QuerySet):
    def update(self, **kwargs):
        if "auto_datetime" in kwargs:
            super(BaseQuerySet, self).update(**kwargs)
        else:
            super(BaseQuerySet, self).update(**kwargs, auto_datetime=timezone.now())


BaseManager = Manager.from_queryset(BaseQuerySet)
