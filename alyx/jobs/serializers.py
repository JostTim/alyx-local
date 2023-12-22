from rest_framework import serializers
from actions.models import Session
from jobs.models import Task
from data.models import DataRepository
from alyx.base import BaseSerializerEnumField


class TaskListSerializer(serializers.HyperlinkedModelSerializer):
    session = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field="id", many=False, queryset=Session.objects.all()
    )
    status = BaseSerializerEnumField(required=False)

    class Meta:
        model = Task
        fields = [
            "session",
            "id",
            "status",
        ]

    @staticmethod
    def setup_eager_loading(queryset):
        """Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related("session", "data_repository")
        queryset = queryset.prefetch_related("parents")
        return queryset.order_by("-start_time")


class TaskDetailsSeriaizer(serializers.HyperlinkedModelSerializer):
    session = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field="id", many=False, queryset=Session.objects.all()
    )

    data_repository = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field="name", many=False, queryset=DataRepository.objects.all()
    )

    parents = serializers.SlugRelatedField(
        read_only=False,
        required=False,
        slug_field="id",
        many=True,
        queryset=Task.objects.all(),
    )

    @staticmethod
    def setup_eager_loading(queryset):
        """Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related("session", "data_repository")
        return queryset.order_by("-start_time")

    class Meta:
        model = Task
        fields = "__all__"
