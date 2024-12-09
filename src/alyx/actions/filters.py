from django.contrib.postgres.fields import JSONField
from django_filters import CharFilter, NumberFilter, BooleanFilter
from django.db.models import Count, ExpressionWrapper, F, Q, FloatField

from ..base.filters import BaseFilterSet, rich_json_filter
from ..experiments.filters import _filter_qs_with_brain_regions
from .models import (
    BaseAction,
    Session,
    WaterAdministration,
    WaterRestriction,
    Weighing,
    WaterType,
    LabLocation,
    Surgery,
    ProcedureType,
)

import structlog

logger = structlog.get_logger("actions.filters")


class SessionFilter(BaseFilterSet):
    subject = CharFilter(field_name="subject__nickname", method="filter_subject")
    dataset_types = CharFilter(field_name="dataset_types", method="filter_dataset_types")
    performance_gte = NumberFilter(field_name="performance", method="filter_performance_gte")
    performance_lte = NumberFilter(field_name="performance", method="filter_performance_lte")
    users = CharFilter(field_name="users__username", method="filter_users")
    date_range = CharFilter(field_name="date_range", method="filter_date_range")
    type = CharFilter(field_name="type", lookup_expr="iexact")
    lab = CharFilter(field_name="lab__name", lookup_expr="iexact")
    task_protocol = CharFilter(field_name="task_protocol", lookup_expr="icontains")
    qc = CharFilter(method="enum_field_filter")
    json = CharFilter(field_name="json", method="filter_json")
    location = CharFilter(field_name="location__name", lookup_expr="icontains")
    extended_qc = CharFilter(field_name="extended_qc", method="filter_extended_qc")
    projects = CharFilter(field_name="projects__name", lookup_expr="icontains")
    # below is an alias to keep compatibility after moving project FK field to projects M2M
    project = CharFilter(field_name="projects__name", lookup_expr="icontains")
    procedures = CharFilter(field_name="procedures", method="filter_procedures")
    exclude_procedures = CharFilter(field_name="procedures", method="filter_exclude_procedures")
    # brain region filters
    atlas_name = CharFilter(field_name="name__icontains", method="atlas")
    atlas_acronym = CharFilter(field_name="acronym__iexact", method="atlas")
    atlas_id = NumberFilter(field_name="pk", method="atlas")
    histology = BooleanFilter(field_name="histology", method="has_histology")
    tag = CharFilter(field_name="tag", method="filter_tag")

    # dataset_object
    object = CharFilter(method="filter_object")

    attribute = CharFilter(method="filter_attribute")

    data_repository = CharFilter(method="filter_data_repository")

    default_data_repository = CharFilter(method="filter_default_data_repository")

    # dataset_attribute : TODO

    def filter_subject(self, queryset, _, value):
        print("SHIEKS", value)
        objects = value.split(",")
        return queryset.filter(subject__nickname__in=objects)

    def filter_object(self, queryset, name, value):
        objects = value.split(",")
        queryset = queryset.filter(data_dataset_session_related__dataset_type__object__in=objects)
        queryset = queryset.annotate(
            dset_objects_count=Count("data_dataset_session_related__dataset_type", distinct=True)
        )
        queryset = queryset.filter(dset_objects_count__gte=len(objects))
        return queryset

    def filter_attribute(self, queryset, name, value):
        attributes = value.split(",")
        queryset = queryset.filter(data_dataset_session_related__dataset_type__attribute__in=attributes)
        queryset = queryset.annotate(
            dset_objects_count=Count("data_dataset_session_related__dataset_type", distinct=True)
        )
        queryset = queryset.filter(dset_objects_count__gte=len(attributes))
        return queryset

    def filter_data_repository(self, queryset, name, value):
        data_repository = value
        queryset = queryset.filter(data_dataset_session_related__data_repository__name=data_repository)
        return queryset

    def filter_default_data_repository(self, queryset, name, value):
        default_data_repository = value
        queryset = queryset.filter(default_data_repository__name=default_data_repository)
        return queryset

    def filter_tag(self, queryset, name, value):
        """
        returns sessions that contain datasets tagged as
        :param queryset:
        :param name:
        :param value:
        :return:
        """
        queryset = queryset.filter(data_dataset_session_related__tags__name__icontains=value).distinct()
        return queryset

    def atlas(self, queryset, name, value):
        """
        returns sessions containing at least one channel in the given brain region.
        Hierarchical tree search"
        """
        return _filter_qs_with_brain_regions(self, queryset, name, value)

    def has_histology(self, queryset, name, value):
        """returns sessions whose subjects have an histology session available"""
        if value:
            fcn_query = queryset.filter
        else:
            fcn_query = queryset.exclude
        return fcn_query(subject__actions_sessions__procedures__name="Histology").distinct()

    def filter_json(self, queryset, name, value):
        return rich_json_filter(queryset, name, value)
        # return base_json_filter("json", queryset, name, value)

    def filter_extended_qc(self, queryset, name, value):
        return rich_json_filter(queryset, name, value)
        # return base_json_filter("extended_qc", queryset, name, value)

    def filter_users(self, queryset, name, value):
        users = value.split(",")
        queryset = queryset.filter(users__username__in=users)
        queryset = queryset.annotate(users_count=Count("users__username"))
        queryset = queryset.filter(users_count__gte=len(users))
        return queryset

    def filter_date_range(self, queryset, name, value):
        drange = value.split(",")
        queryset = queryset.filter(
            Q(start_time__date__gte=drange[0]),
            Q(start_time__date__lte=drange[1]),
        )
        return queryset

    def filter_dataset_types(self, queryset, name, value):
        dtypes = value.split(",")
        queryset = queryset.filter(data_dataset_session_related__dataset_type__name__in=dtypes)
        queryset = queryset.annotate(dtypes_count=Count("data_dataset_session_related__dataset_type", distinct=True))
        queryset = queryset.filter(dtypes_count__gte=len(dtypes))
        return queryset

    def filter_procedures(self, queryset, name, value):
        procedures_names = value.split(",")
        logger.warning(f"Filtering for {procedures_names} in filter_procedures")
        q_objects = Q()

        for procedures_name in procedures_names:
            logger.warning(f"Filtering for {procedures_name}")
            q_objects &= Q(procedures__name__icontains=procedures_name)
        return queryset.filter(q_objects)

    def filter_exclude_procedures(self, queryset, name, value):
        excluded_procedures_names = value.split(",")
        logger.warning(f"Excluding {excluded_procedures_names} in filter_exclude_procedures")
        q_objects = Q()

        for excluded_procedure_name in excluded_procedures_names:
            logger.warning(f"Excluding {excluded_procedure_name}")
            q_objects |= Q(procedures__name__icontains=excluded_procedure_name)

        return queryset.exclude(q_objects)

    def filter_performance_gte(self, queryset, name, perf):
        queryset = queryset.exclude(n_trials__isnull=True)
        pf = ExpressionWrapper(100 * F("n_correct_trials") / F("n_trials"), output_field=FloatField())
        queryset = queryset.annotate(performance=pf)
        return queryset.filter(performance__gte=float(perf))

    def filter_performance_lte(self, queryset, name, perf):
        queryset = queryset.exclude(n_trials__isnull=True)
        pf = ExpressionWrapper(100 * F("n_correct_trials") / F("n_trials"), output_field=FloatField())
        queryset = queryset.annotate(performance=pf)
        return queryset.filter(performance__lte=float(perf))

    class Meta:
        model = Session
        exclude = []
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class WeighingFilter(BaseFilterSet):
    nickname = CharFilter(field_name="subject__nickname", lookup_expr="iexact")

    class Meta:
        model = Weighing
        exclude = ["json"]


class WaterAdministrationFilter(BaseFilterSet):
    nickname = CharFilter(field_name="subject__nickname", lookup_expr="iexact")

    class Meta:
        model = WaterAdministration
        exclude = ["json"]


class WaterRestrictionFilter(BaseFilterSet):
    subject = CharFilter(field_name="subject__nickname", lookup_expr="iexact")

    class Meta:
        model = WaterRestriction
        exclude = ["json"]
