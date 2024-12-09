from rest_framework import generics
from django_filters.rest_framework import CharFilter, UUIDFilter, NumberFilter
from django.db.models import F, Func, Value, CharField, functions, Q


from ..base.filters import BaseFilterSet
from ..base.permissions import rest_permission_classes
from ..data.models import Dataset
from .models import ProbeInsertion, TrajectoryEstimate, Channel, BrainRegion
from .serializers import (
    ProbeInsertionListSerializer,
    ProbeInsertionDetailSerializer,
    TrajectoryEstimateSerializer,
    ChannelSerializer,
    BrainRegionSerializer,
)
from .filters import BrainRegionFilter, ChannelFilter, TrajectoryEstimateFilter, ProbeInsertionFilter

"""
Probe insertion objects REST filters and views
"""


class ProbeInsertionList(generics.ListCreateAPIView):
    """
    get: **FILTERS**

    -   **name**: probe insertion name `/trajectories?name=probe00`
    -   **subject**: subject nickname: `/insertions?subject=Algernon`
    -   **date**: session date: `/inssertions?date=2020-01-15`
    -   **experiment_number**: session number `/insertions?experiment_number=1`
    -   **session**: session UUID`/insertions?session=aad23144-0e52-4eac-80c5-c4ee2decb198`
    -   **task_protocol** (icontains)
    -   **location**: location name (icontains)
    -   **project**: project name (icontains)
    -   **model**: probe model name `/insertions?model=3A`
    -   **dataset_type**: contains dataset type `/insertions?dataset_type=clusters.metrics`
    -   **no_dataset_type**: doesn't contain dataset type
    `/insertions?no_dataset_type=clusters.metrics`
    -   **atlas_name**: returns a session if any channel name icontains
     the value: `/insertions?brain_region=visual cortex`
    -   **atlas_acronym**: returns a session if any of its channels name exactly
     matches the value `/insertions?atlas_acronym=SSp-m4`, cf Allen CCFv2017
    -   **atlas_id**: returns a session if any of its channels id matches the
     provided value: `/insertions?atlas_id=950`, cf Allen CCFv2017

    [===> probe insertion model reference](/admin/doc/models/experiments.probeinsertion)
    """

    queryset = ProbeInsertion.objects.all()
    queryset = ProbeInsertionListSerializer.setup_eager_loading(queryset)
    serializer_class = ProbeInsertionListSerializer
    permission_classes = rest_permission_classes()
    filterset_class = ProbeInsertionFilter


class ProbeInsertionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProbeInsertion.objects.all()
    serializer_class = ProbeInsertionDetailSerializer
    permission_classes = rest_permission_classes()


"""
Trajectory Estimates objects REST filters and views
"""


class TrajectoryEstimateList(generics.ListCreateAPIView):
    """
    get: **FILTERS**

    -   **provenance**: probe insertion provenance
        must one of the strings among those choices:
        'Ephys aligned histology track', 'Histology track', 'Micro-manipulator', 'Planned'
        `/trajectories?provenance=Planned`
    -   **subject: subject nickname: `/trajectories?subject=Algernon`
    -   **date**: session date: `/trajectories?date=2020-01-15`
    -   **experiment_number**: session number `/trajectories?experiment_number=1`
    -   **session**: `/trajectories?session=aad23144-0e52-4eac-80c5-c4ee2decb198`
    -   **probe**: probe_insertion name `/trajectories?probe=probe01`

    [===> trajectory model reference](/admin/doc/models/experiments.trajectoryestimate)
    """

    queryset = TrajectoryEstimate.objects.all()
    serializer_class = TrajectoryEstimateSerializer
    permission_classes = rest_permission_classes()
    filterset_class = TrajectoryEstimateFilter


class TrajectoryEstimateDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = TrajectoryEstimate.objects.all()
    serializer_class = TrajectoryEstimateSerializer
    permission_classes = rest_permission_classes()


class ChannelList(generics.ListCreateAPIView):
    """
    get: **FILTERS**

    -   **subject**: subject nickname: `/channels?subject=Algernon`
    -   **session**: UUID `/channels?session=aad23144-0e52-4eac-80c5-c4ee2decb198`
    -   **lab**: lab name `/channels?lab=wittenlab`
    -   **probe_insertion**: UUID  `/channels?probe_insertion=aad23144-0e52-4eac-80c5-c4ee2decb198`

    [===> channel model reference](/admin/doc/models/experiments.channel)
    """

    def get_serializer(self, *args, **kwargs):
        """if an array is passed, set serializer to many"""
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(generics.ListCreateAPIView, self).get_serializer(*args, **kwargs)

    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = rest_permission_classes()
    filterset_class = ChannelFilter


class ChannelDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = rest_permission_classes()


class BrainRegionList(generics.ListAPIView):
    """
    get: **FILTERS**

    -   **id**: Allen primary key: `/brain-regions?id=687`
    -   **acronym**: iexact on acronym `/brain-regions?acronym=RSPv5`
    -   **name**: icontains on name `/brain-regions?name=retrosplenial`
    -   **description**: icontains on description `/brain-regions?description=RSPv5`
    -   **parent**: get child nodes `/brain-regions?parent=315`
    -   **ancestors**: get all ancestors for a given ID
    -   **descendants**: get all descendants for a given ID

    [===> brain region model reference](/admin/doc/models/experiments.brainregion)
    """

    queryset = BrainRegion.objects.all()
    serializer_class = BrainRegionSerializer
    permission_classes = rest_permission_classes()
    filterset_class = BrainRegionFilter


class BrainRegionDetail(generics.RetrieveUpdateAPIView):
    queryset = BrainRegion.objects.all()
    serializer_class = BrainRegionSerializer
    permission_classes = rest_permission_classes()
