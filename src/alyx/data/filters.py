from django_filters import CharFilter, DateTimeFilter, UUIDFilter, BooleanFilter
import os

from ..base.base import BaseFilterSet
from ..experiments.models import ProbeInsertion
from .models import Download, FileRecord, Dataset, DataRepository


class DataRepositoryFilter(BaseFilterSet):
    data_path = CharFilter(method="filter_data_path")
    globus_path = CharFilter(field_name="globus_path")
    hostname = CharFilter(field_name="hostname")
    name = CharFilter(field_name="name")
    id = CharFilter(field_name="id")

    def filter_data_path(self, queryset, name, value):
        value = os.path.normpath(value)
        values = [split for split in value.split(os.sep) if split != ""]
        hostname = values[0]
        path = os.sep + os.sep.join(values[1:])
        return queryset.filter(hostname=hostname).filter(globus_path=path)


class DatasetFilter(BaseFilterSet):
    subject = CharFilter("session__subject__nickname")
    lab = CharFilter("session__lab__name")
    created_date = CharFilter("created_datetime__date")
    date = CharFilter("session__start_time__date")
    created_by = CharFilter("created_by__username")
    dataset_type = CharFilter("dataset_type__name")
    experiment_number = CharFilter("session__number")
    created_date_gte = DateTimeFilter("created_datetime__date", lookup_expr="gte")
    created_date_lte = DateTimeFilter("created_datetime__date", lookup_expr="lte")
    exists = BooleanFilter(method="filter_exists")
    probe_insertion = UUIDFilter(method="probe_insertion_filter")
    public = BooleanFilter(method="filter_public")
    protected = BooleanFilter(method="filter_protected")
    tag = CharFilter("tags__name")
    revision = CharFilter("revision__name")
    data_repository = CharFilter("data_repository__name")

    class Meta:
        model = Dataset
        exclude = ["json"]

    def filter_exists(self, dsets, name, value):
        """
        Filters datasets for which at least one file record Globus not personal exists.
        Only if the database has any globus non-personal repositories (ie. servers)
        """
        if len(DataRepository.objects.filter(globus_is_personal=False)) > 0:
            frs = FileRecord.objects.filter(pk__in=dsets.values_list("file_records", flat=True))
            pkd = frs.filter(exists=value).values_list("dataset", flat=True)
            dsets = dsets.filter(pk__in=pkd)
        return dsets

    def probe_insertion_filter(self, dsets, _, pk):
        """
        Filter datasets that have collection name the same as probe id
        """
        probe = ProbeInsertion.objects.get(pk=pk)
        dsets = dsets.filter(session=probe.session, collection__icontains=probe.name)
        return dsets

    def filter_public(self, dsets, name, value):
        if value:
            return dsets.filter(tags__public=True).distinct()
        else:
            return dsets.exclude(tags__public=True)

    def filter_protected(self, dsets, name, value):
        if value:
            return dsets.filter(tags__protected=True).distinct()
        else:
            return dsets.exclude(tags__protected=True)


class FileRecordFilter(BaseFilterSet):
    lab = CharFilter("dataset__session__lab__name")

    data_repository = CharFilter(field_name="dataset__data_repository__name")

    class Meta:
        model = FileRecord
        exclude = ["json"]


class DownloadFilter(BaseFilterSet):
    json = CharFilter(field_name="json", lookup_expr=("icontains"))
    dataset = CharFilter("dataset__name")
    user = CharFilter("user__username")
    dataset_type = CharFilter(field_name="dataset__dataset_type__name", lookup_expr=("icontains"))

    class Meta:
        model = Download
        fields = ("count",)
