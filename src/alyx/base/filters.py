from django.db.models import QuerySet, JSONField
from django_filters import CharFilter
from django_filters.rest_framework import FilterSet
from django.contrib.admin import SimpleListFilter
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from rest_framework.views import exception_handler
from rest_framework.exceptions import ParseError


import json, re

import structlog

logger = structlog.get_logger("base.filters")


class DefaultListFilter(SimpleListFilter):
    # Default filter value.
    # http://stackoverflow.com/a/16556771/1595060
    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": cl.get_query_string(
                    {
                        self.parameter_name: lookup,
                    },
                    [],
                ),
                "display": title,
            }


class BaseFilterSet(FilterSet):
    """
    Base class for Alyx filters. Adds a custom django filter for extensible queries using
    Django syntax. For example this is a query on a start_time field of a REST accessible model:
    sessions?django=start_time__date__lt,2017-06-05'
    if a ~ is prepended to the field name, performs an exclude instead of a filter
    sessions?django=~start_time__date__lt,2017-06-05'
    """

    django = CharFilter(field_name="", method="django_filter")

    def django_filter(self, queryset, _, value):
        kwargs = _custom_filter_parser(value)
        for k in kwargs:
            if k.startswith("~"):
                queryset = queryset.exclude(**{k[1:]: kwargs[k]}).distinct()
            else:
                queryset = queryset.filter(**{k: kwargs[k]}).distinct()
        return queryset

    def enum_field_filter(self, queryset, name, value):
        """
        Method to be used in the filterset class for enum fields
        """
        choices = queryset.model._meta.get_field(name).choices
        # create a dictionary string -> integer
        value_map = {v.lower(): k for k, v in choices}
        # get the integer value for the input string
        try:
            value = value_map[value.lower().strip()]
        except KeyError:
            raise ValueError("Invalid" + name + ", choices are: " + ", ".join([ch[1] for ch in choices]))
        return queryset.filter(**{name: value})

    @classmethod
    def filter_for_lookup(cls, f, lookup_type):
        # override date range lookups
        if isinstance(f, JSONField) and lookup_type == "exact":
            return CharFilter, {}

        # use default behavior otherwise
        return super().filter_for_lookup(f, lookup_type)

    class Meta:
        abstract = True


class SortedRelatedDropdownFilter(RelatedDropdownFilter):
    def field_choices(self, field, request, model_admin):
        related_model = field.related_model
        human_readable_name = related_model.human_field_string()

        related_ids = model_admin.model.objects.values_list(f"{field.name}__id", flat=True).distinct()
        choices = (
            related_model.objects.filter(id__in=related_ids)
            .order_by(human_readable_name)
            .values_list("id", human_readable_name)
        )
        return list(choices)


class ActiveFilter(DefaultListFilter):
    title = "active"
    parameter_name = "active"

    def lookups(self, request, model_admin):
        return (
            (None, "All"),
            ("active", "Active"),
        )

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(
                start_time__isnull=False,
                end_time__isnull=True,
            )
        elif self.value is None:
            return queryset.all()


class CreatedByListFilter(DefaultListFilter):
    title = "users"
    parameter_name = "users"

    def lookups(self, request, model_admin):
        return (
            (None, "Me"),
            ("all", "All"),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(users=request.user)
        elif self.value == "all":
            return queryset.all()


def rest_filters_exception_handler(exc, context):
    """
    Custom exception handler that provides context (field names etc...) for poorly formed
    REST queries
    """
    response = exception_handler(exc, context)

    from rest_framework.response import Response

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data["status_code"] = response.status_code
    else:
        data = {"status_code": 500, "detail": str(exc)}
        response = Response(data, status=500)

    return response


def rich_json_filter(queryset: QuerySet, name: str, value: str):
    """
    function that filters the queryset from a custom REST query. To be used directly as
    a method for a FilterSet object. For example:
    # exact/equal lookup: "?extended_qc=qc_bool,True"
    # gte lookup: "?extended_qc=qc_pct__gte,0.5"
    # chained lookups: "?extended_qc=qc_pct__gte,0.5;qc_bool,True"
    """
    pattern = re.compile(r"(?P<json_keys>^[\w \+]+),(?P<json_value>.*$)")

    logger.warning(f"About to filter {name} with values {value}")

    filters = value.split(";")
    for filter in filters:
        logger.warning(f"Will filter {filter}")
        match = pattern.match(filter)

        if match is None:
            logger.warning(f"{name} filter {filter} was not parseable.")
            raise ParseError(f"{name} filter {filter} was not parseable.")

        logger.warning(f"Values are {match['json_value']}")

        json_keys = match["json_keys"]

        try:
            value = json.loads(match["json_value"])
        except json.JSONDecodeError:
            value = match["json_value"]

        if "__not" in json_keys:
            json_keys = json_keys.replace("__not", "")
            method = "exclude"
        else:
            method = "filter"

        logger.warning(f"Filtering query with {name}__{json_keys}={value}")

        # Assumes that the left side is the "key" and the right side is the "value"
        queryset = getattr(queryset, method)(**{f"{name}__{json_keys}": value})

    return queryset


def base_json_filter(fieldname, queryset, _, value):
    """
    function that filters the queryset from a custom REST query. To be used directly as
    a method for a FilterSet object. For example:
    # exact/equal lookup: "?extended_qc=qc_bool,True"
    # gte lookup: "?extended_qc=qc_pct__gte,0.5"
    # chained lookups: "?extended_qc=qc_pct__gte,0.5;qc_bool,True"
    """
    kwargs = _custom_filter_parser(value, arg_prefix=fieldname + "__")
    queryset = queryset.filter(**kwargs)
    return queryset


def split_comma_outside_brackets(value):
    """For custom filters splits by comma if they are not within brackets. See
    test_base.py for examples"""
    fv = []
    word = ""
    close_char = ""
    for c in value:
        if c == "," and close_char == "":
            fv.append(word)
            word = ""
            continue
        elif c == "[":
            close_char = "]"
        elif c == "(":
            close_char = ")"
        elif c == close_char:
            close_char = ""
        word += c
    fv.append(word)
    return fv


def _custom_filter_parser(value, arg_prefix=""):
    """
    # parses the value string provided to custom filters json and Django via REST api
    :param value: string returned by the rest request: examples:
        "qc_pct__gte,0.5,qc_bool,True"
         "myfield,[4, 9]]"
    :param arg_prefix:
    :return: dictionary that can be fed directly to a Django filter() query
    """
    # split by commas only if they are outside list brackets (I know... we all love regex)
    fv = split_comma_outside_brackets(value)
    i = 0
    out_dict = {}
    while i < len(fv):
        field, val = fv[i], fv[i + 1]
        i += 2
        if val == "None":
            val = None
        elif val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        elif val.replace(".", "", 1).isdigit():
            val = float(val)
        elif val.startswith(("(", "[")) and val.endswith((")", "]")):
            val = eval(val)
        if arg_prefix + field in out_dict:
            raise ValueError('Duplicated fields in "' + str(value) + '"')
        out_dict[arg_prefix + field] = val
    return out_dict
