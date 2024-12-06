from django_filters.rest_framework import CharFilter, UUIDFilter, NumberFilter
from django.db.models import F, Func, Value, CharField, functions, Q

from ..base.base import BaseFilterSet

from ..data.models import Dataset
from .models import ProbeInsertion, TrajectoryEstimate, Channel, BrainRegion


def _filter_qs_with_brain_regions(self, queryset, region_field, region_value):
    brs = BrainRegion.objects.filter(**{region_field: region_value}).get_descendants(include_self=True)
    qs_trajs = (
        TrajectoryEstimate.objects.filter(provenance__gte=70)
        .prefetch_related("channels__brain_region")
        .filter(channels__brain_region__in=brs)
        .distinct()
    )
    if queryset.model.__name__ == "Session":
        qs = queryset.prefetch_related("probe_insertion__trajectory_estimate").filter(
            probe_insertion__trajectory_estimate__in=qs_trajs
        )
    elif queryset.model.__name__ == "ProbeInsertion":
        qs = queryset.prefetch_related("trajectory_estimate").filter(trajectory_estimate__in=qs_trajs)
    return qs


class ProbeInsertionFilter(BaseFilterSet):
    subject = CharFilter("session__subject__nickname")
    date = CharFilter("session__start_time__date")
    experiment_number = CharFilter("session__number")
    name = CharFilter("name")
    session = UUIDFilter("session")
    model = CharFilter("model__name")
    dataset_type = CharFilter(method="dtype_exists")
    no_dataset_type = CharFilter(method="dtype_not_exists")
    project = CharFilter(field_name="session__project__name", lookup_expr="icontains")
    task_protocol = CharFilter(field_name="session__task_protocol", lookup_expr="icontains")
    # brain region filters
    atlas_name = CharFilter(field_name="name__icontains", method="atlas")
    atlas_acronym = CharFilter(field_name="acronym__iexact", method="atlas")
    atlas_id = NumberFilter(field_name="pk", method="atlas")

    def atlas(self, queryset, name, value):
        """
        returns sessions containing at least one channel in the given brain region.
        Hierarchical tree search"
        """
        return _filter_qs_with_brain_regions(self, queryset, name, value)

    def dtype_exists(self, probes, _, dtype_name):
        """
        Filter for probe insertions that contain specified dataset type
        """
        dsets = Dataset.objects.filter(dataset_type__name=dtype_name)

        # Annotate with new column that contains unique session, probe name
        dsets = dsets.annotate(
            session_probe_name=functions.Concat(
                functions.Cast(F("session"), output_field=CharField()),
                Func(F("collection"), Value("/"), Value(2), function="split_part"),
                output_field=CharField(),
            )
        )

        probes = probes.annotate(
            session_probe_name=functions.Concat(
                functions.Cast(F("session"), output_field=CharField()), F("name"), output_field=CharField()
            )
        )

        queryset = probes.filter(session_probe_name__in=dsets.values_list("session_probe_name", flat=True))
        return queryset

    def dtype_not_exists(self, probes, _, dtype_name):
        """
        Filter for probe insertions that don't contain specified dataset type
        """

        dsets = Dataset.objects.filter(dataset_type__name=dtype_name)

        # Annotate with new column that contains unique session, probe name
        dsets = dsets.annotate(
            session_probe_name=functions.Concat(
                functions.Cast(F("session"), output_field=CharField()),
                Func(F("collection"), Value("/"), Value(2), function="split_part"),
                output_field=CharField(),
            )
        )

        probes = probes.annotate(
            session_probe_name=functions.Concat(
                functions.Cast(F("session"), output_field=CharField()), F("name"), output_field=CharField()
            )
        )

        queryset = probes.filter(~Q(session_probe_name__in=dsets.values_list("session_probe_name", flat=True)))
        return queryset

    class Meta:
        model = ProbeInsertion
        exclude = ["json"]


class TrajectoryEstimateFilter(BaseFilterSet):
    provenance = CharFilter(method="enum_field_filter")
    subject = CharFilter("probe_insertion__session__subject__nickname")
    project = CharFilter("probe_insertion__session__projects__name")
    date = CharFilter("probe_insertion__session__start_time__date")
    experiment_number = CharFilter("probe_insertion__session__number")
    session = UUIDFilter("probe_insertion__session__id")
    probe = CharFilter("probe_insertion__name")

    class Meta:
        model = TrajectoryEstimate
        exclude = ["json"]


class ChannelFilter(BaseFilterSet):
    session = UUIDFilter("trajectory_estimate__probe_insertion__session")
    probe_insertion = UUIDFilter("trajectory_estimate__probe_insertion")
    subject = CharFilter("trajectory_estimate__probe_insertion__session__subject__nickname")
    lab = CharFilter("trajectory_estimate__probe_insertion__session__lab__name")

    class Meta:
        model = Channel
        exclude = ["json"]


class BrainRegionFilter(BaseFilterSet):
    acronym = CharFilter(lookup_expr="iexact")
    description = CharFilter(lookup_expr="icontains")
    name = CharFilter(lookup_expr="icontains")
    ancestors = CharFilter(field_name="ancestors", method="filter_ancestors")
    descendants = CharFilter(field_name="descendants", method="filter_descendants")

    class Meta:
        model = BrainRegion
        fields = ("id", "acronym", "description", "name", "parent")

    def filter_descendants(self, queryset, _, pk):
        r = BrainRegion.objects.get(pk=pk) if pk.isdigit() else BrainRegion.objects.get(acronym=pk)
        return r.get_descendants(include_self=True).exclude(id=0)

    def filter_ancestors(self, queryset, _, pk):
        r = BrainRegion.objects.get(pk=pk) if pk.isdigit() else BrainRegion.objects.get(acronym=pk)
        return r.get_ancestors(include_self=True).exclude(pk=0)
