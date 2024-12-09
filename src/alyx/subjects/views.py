from rest_framework import generics

from ..base.permissions import rest_permission_classes
from .models import Subject, Project
from .serializers import (
    SubjectListSerializer,
    SubjectDetailSerializer,
    WaterRestrictedSubjectListSerializer,
    ProjectSerializer,
)
from .filters import SubjectFilter


class SubjectList(generics.ListCreateAPIView):
    queryset = Subject.objects.all()
    queryset = SubjectListSerializer.setup_eager_loading(queryset)
    serializer_class = SubjectListSerializer
    permission_classes = rest_permission_classes()
    filterset_class = SubjectFilter


class SubjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectDetailSerializer
    permission_classes = rest_permission_classes()
    lookup_field = "nickname"


class ProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = rest_permission_classes()
    lookup_field = "name"


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = rest_permission_classes()
    lookup_field = "name"


class WaterRestrictedSubjectList(generics.ListAPIView):
    queryset = Subject.objects.all().extra(
        where=[
            """
        subjects_subject.id IN
        (SELECT subject_id FROM actions_waterrestriction
         WHERE end_time IS NULL)"""
        ]
    )
    serializer_class = WaterRestrictedSubjectListSerializer
    permission_classes = rest_permission_classes()
