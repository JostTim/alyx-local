from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Count, Q, BooleanField

from .models import (
    DataRepositoryType,
    DataRepository,
    DataFormat,
    DatasetType,
    Dataset,
    Download,
    FileRecord,
    Revision,
    Tag,
)
from .transfers import _get_session, _change_default_dataset
from ..base.admins import get_admin_url
from ..actions.models import Session
from ..subjects.models import Subject
from ..misc.models import LabMember
from uuid import UUID
import structlog

logger = structlog.get_logger("data/serializers")


class DataRepositoryTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataRepositoryType
        fields = "__all__"
        extra_kwargs = {"url": {"view_name": "datarepositorytype-detail", "lookup_field": "name"}}


class DataRepositorySerializer(serializers.HyperlinkedModelSerializer):
    repository_type = serializers.SlugRelatedField(
        read_only=False, slug_field="name", queryset=DataRepositoryType.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = DataRepository
        fields = ("id", "name", "timezone", "globus_path", "hostname", "data_path", "repository_type", "json")
        extra_kwargs = {"url": {"view_name": "datarepository-detail", "lookup_field": "name"}}


class DataFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFormat
        fields = "__all__"
        extra_kwargs = {"url": {"view_name": "dataformat-detail", "lookup_field": "name"}}


class DatasetTypeSerializer(serializers.HyperlinkedModelSerializer):
    created_by = serializers.SlugRelatedField(
        read_only=False,
        slug_field="username",
        queryset=get_user_model().objects.all(),
        allow_null=True,
        required=False,
        default=serializers.CurrentUserDefault(),
    )

    admin_url = serializers.SerializerMethodField()

    def get_admin_url(self, obj):
        return get_admin_url(obj)

    class Meta:
        model = DatasetType
        fields = ("id", "name", "created_by", "description", "filename_pattern", "object", "attribute", "admin_url")
        extra_kwargs = {"url": {"view_name": "datasettype-detail", "lookup_field": "name"}}


class FileRecordSerializer(serializers.HyperlinkedModelSerializer):
    dataset = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Dataset.objects.all())

    admin_url = serializers.SerializerMethodField()

    extra = serializers.CharField(required=False, allow_blank=True, max_length=255)

    exists = serializers.BooleanField(required=False, allow_null=True)

    hash = serializers.CharField(required=False, allow_null=True)

    @staticmethod
    def setup_eager_loading(queryset):
        """Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related("dataset")
        return queryset

    def get_admin_url(self, obj):
        return get_admin_url(obj)

    class Meta:
        model = FileRecord
        fields = [
            "id",
            "url",
            "admin_url",
            "dataset",
            "json",
            "file_name",
            "full_path",
            "relative_path",
            "exists",
            "hash",
            # ALF parts :
            "remote_root",
            "attribute",
            "object",
            "extension",
            "revision",
            "collection",
            "subject",
            "date",
            "number",
            "extra",
        ]


class DatasetFileRecordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileRecord
        fields = ("id", "relative_path", "extra", "exists", "file_name", "hash")

    # @staticmethod No longer necessary, but may be implemented elsewere to improve performance while getting
    # FileRecord components
    # def setup_eager_loading(queryset):
    #     """ Perform necessary eager loading of data to avoid horrible performance."""
    #     queryset = queryset.select_related('data_repository', 'data_repository__globus_path') "
    #     this only makes fething the related fields a single query process. As we don't fetch related fields anymore
    # here it isn't necessary. We can do this for other models though"
    #     return queryset


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    dataset_type_pk = serializers.PrimaryKeyRelatedField(
        source="dataset_type",
        read_only=False,
        required=False,
        queryset=DatasetType.objects.all(),
    )

    data_format_pk = serializers.PrimaryKeyRelatedField(
        source="data_format",
        read_only=False,
        required=False,
        queryset=DataFormat.objects.all(),
    )

    session_pk = serializers.PrimaryKeyRelatedField(
        source="session",
        read_only=False,
        required=False,
        queryset=Session.objects.all(),
    )

    data_repository_pk = serializers.PrimaryKeyRelatedField(
        read_only=False, required=False, source="data_repository", queryset=DataRepository.objects.all()
    )

    created_by = serializers.SlugRelatedField(
        read_only=False,
        slug_field="username",
        required=False,
        queryset=get_user_model().objects.all(),
        default=serializers.CurrentUserDefault(),
    )

    revision_pk = serializers.PrimaryKeyRelatedField(
        read_only=False, required=False, source="revision", queryset=Revision.objects.all()
    )

    data_format = serializers.SlugRelatedField(
        read_only=False,
        required=False,
        slug_field="file_extension",
        queryset=DataFormat.objects.all(),
    )

    dataset_type = serializers.SlugRelatedField(
        read_only=False,
        slug_field="name",
        required=False,
        queryset=DatasetType.objects.all(),
    )

    session = serializers.SlugRelatedField(
        read_only=True,
        required=False,
        slug_field="u_alias",
    )

    revision = serializers.SerializerMethodField()

    # session = serializers.HyperlinkedRelatedField(
    #    read_only=False, required=False, view_name="session-detail",
    #    queryset=Session.objects.all(),
    # )

    tags = serializers.SlugRelatedField(
        read_only=False, required=False, many=True, slug_field="name", queryset=Tag.objects.all()
    )

    version = serializers.CharField(required=False, allow_null=True)
    file_size = serializers.IntegerField(required=False, allow_null=True)
    collection = serializers.CharField(required=False, allow_blank=True, max_length=255)

    data_repository = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field="name", queryset=DataRepository.objects.all()
    )

    default_dataset = serializers.BooleanField(required=False, allow_null=True)
    public = serializers.ReadOnlyField()
    protected = serializers.ReadOnlyField()
    file_records = DatasetFileRecordsSerializer(read_only=True, many=True)

    # If session is not provided, use subject, start_time, number
    # subject = serializers.SlugRelatedField(
    #     write_only=True, required=False, slug_field='nickname',
    #     queryset=Subject.objects.all(),
    # )

    date = serializers.DateField(required=False)

    number = serializers.IntegerField(required=False)

    admin_url = serializers.SerializerMethodField()

    def get_revision(self, obj):
        return obj.revision.name if obj.revision is not None else ""

    def get_admin_url(self, obj):
        return get_admin_url(obj)

    @staticmethod
    def setup_eager_loading(queryset):
        """Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related(
            "created_by", "dataset_type", "data_format", "session", "data_repository", "revision"
        )
        queryset = queryset.prefetch_related(
            "file_records",
            "tags",
        )
        public = Count("tags", filter=Q(tags__public=True), output_field=BooleanField())
        protected = Count("tags", filter=Q(tags__protected=True), output_field=BooleanField())
        queryset = queryset.annotate(public=public, protected=protected)
        return queryset

    def create(self, validated_data):
        # Get out some useful info
        # revision = validated_data.get('revision', None)
        collection = validated_data.get("collection", None)
        dataset_type = validated_data.get("dataset_type", None)
        default = validated_data.get("default_dataset", None)
        session = validated_data.get("session", None)

        if session:
            if default is True:
                _change_default_dataset(session, collection, dataset_type)
                validated_data["default_dataset"] = True
            return super(DatasetSerializer, self).create(validated_data)

        # Find or create an appropriate session for the dataset as session was not supplied.
        subject = validated_data.pop("subject", None)
        date = validated_data.pop("date", None)
        number = validated_data.pop("number", None)
        if not subject or not date or not number:
            return super(DatasetSerializer, self).create(validated_data)

        # Only get or create the appropriate session if at least the subject and
        # date and number are provided.
        user = validated_data.pop("created_by", None)
        session = _get_session(subject=subject, date=date, number=number, user=user)

        # Create the dataset, attached to the subsession.
        validated_data["session"] = session
        if default is True:
            _change_default_dataset(session, collection, dataset_type)
            validated_data["default_dataset"] = True

        return super(DatasetSerializer, self).create(validated_data)

    class Meta:
        model = Dataset
        fields = (
            "id",
            "url",
            "admin_url",
            "name",
            "created_by",
            "created_datetime",
            "data_repository",
            "file_size",
            "version",
            "auto_datetime",
            "dataset_type",
            "default_dataset",
            "protected",
            "public",
            "tags",
            "session",
            "data_format",
            ## RELATED PK
            "data_repository_pk",
            "data_format_pk",
            "revision_pk",
            "dataset_type_pk",
            "session_pk",
            ## ALF PARTS (except extra)
            "remote_root",
            "subject",
            "date",
            "number",
            "collection",
            "revision",
            "object",
            "attribute",
            "extension",
            ##LIST OF FILE RECORDS
            "file_records",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if ("collection" not in representation.keys()) or representation["collection"] is None:
            representation["collection"] = ""
        return representation


class DownloadSerializer(serializers.HyperlinkedModelSerializer):
    # dataset = DatasetSerializer(many=False, read_only=True)
    dataset = serializers.PrimaryKeyRelatedField(many=False, read_only=True)

    user = serializers.SlugRelatedField(read_only=False, slug_field="username", queryset=LabMember.objects.all())

    class Meta:
        model = Download
        fields = ("id", "user", "dataset", "count", "json")


class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revision
        fields = "__all__"
