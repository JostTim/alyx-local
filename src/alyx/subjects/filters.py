from django_filters import BooleanFilter, CharFilter
from ..base.base import BaseFilterSet
from .models import Subject


class SubjectFilter(BaseFilterSet):
    alive = BooleanFilter("cull", lookup_expr="isnull")
    responsible_user = CharFilter("responsible_user__username")
    stock = BooleanFilter("responsible_user", method="filter_stock")
    water_restricted = BooleanFilter(method="filter_water_restricted")
    lab = CharFilter("lab__name")
    project = CharFilter("projects__name")

    def filter_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(responsible_user__is_stock_manager=True)
        else:
            return queryset.exclude(responsible_user__is_stock_manager=True)

    def filter_water_restricted(self, queryset, name, value):
        if value is True:
            qs = queryset.extra(
                where=[
                    """
                subjects_subject.id IN
                (SELECT subject_id FROM actions_waterrestriction
                WHERE end_time IS NULL)
                """
                ]
            )
        else:
            qs = queryset.extra(
                where=[
                    """
                subjects_subject.id NOT IN
                (SELECT subject_id FROM actions_waterrestriction
                WHERE end_time IS NULL)
                """
                ]
            )
        return qs.filter(cull__isnull=True)

    class Meta:
        model = Subject
        exclude = ["json"]
