from rest_framework import serializers
from ..actions.models import Session
from ..jobs.models import Task
from ..data.models import DataRepository
from ..base.serializers import BaseSerializerEnumField


class TaskListSerializer(serializers.ModelSerializer):
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
        # queryset = queryset.prefetch_related("parents")
        return queryset.order_by("level", "-priority", "-datetime")


class TaskDetailsSeriaizer(serializers.ModelSerializer):
    session = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field="id", many=False, queryset=Session.objects.all()
    )

    data_repository = serializers.SlugRelatedField(
        read_only=False,
        allow_null=True,
        required=False,
        slug_field="name",
        many=False,
        queryset=DataRepository.objects.all(),
    )

    parents = serializers.SlugRelatedField(
        read_only=False,
        allow_null=True,
        required=False,
        slug_field="id",
        many=True,
        queryset=Task.objects.all(),
    )

    status = BaseSerializerEnumField(required=False)

    session_path = serializers.CharField(read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        """Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related("session", "data_repository")
        return queryset.order_by("level", "-priority", "-datetime")

    class Meta:
        model = Task
        fields = "__all__"
