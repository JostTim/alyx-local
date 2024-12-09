from django_filters.rest_framework import CharFilter
from django_filters import FilterSet
from ..base.filters import BaseFilterSet

from .models import Task
from ..actions.models import Session


class TaskFilter(BaseFilterSet):
    lab = CharFilter("session__lab__name")
    status = CharFilter(method="enum_field_filter")

    class Meta:
        model = Task
        exclude = ["json"]


class ProjectFilter(FilterSet):
    """
    Filter used in combobox of task admin page
    """

    class Meta:
        model = Session
        fields = ["projects"]
        exclude = ["json"]

    def __init__(self, *args, **kwargs):
        super(ProjectFilter, self).__init__(*args, **kwargs)
