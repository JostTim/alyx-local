from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Count, Q, BooleanField

from .models import (DataRepositoryType, DataRepository, DataFormat, DatasetType,
                     Dataset, Download, FileRecord, Revision, Tag)
from .transfers import _get_session, _change_default_dataset
from alyx.base import get_admin_url
from actions.models import Session
from subjects.models import Subject
from misc.models import LabMember
from uuid import UUID
import structlog

logger = structlog.get_logger("data/serializers")
class DataRepositoryTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataRepositoryType
        fields = '__all__'
        extra_kwargs = {'url': {'view_name': 'datarepositorytype-detail', 'lookup_field': 'name'}}


class DataRepositorySerializer(serializers.HyperlinkedModelSerializer):

    repository_type = serializers.SlugRelatedField(
        read_only=False,
        slug_field='name',
        queryset=DataRepositoryType.objects.all(),
        allow_null=True,
        required=False)

    class Meta:
        model = DataRepository
        fields = ('id', 'name', 'timezone', 'globus_path', 'hostname', 'data_path', 'repository_type', 'json')
        extra_kwargs = {'url': {'view_name': 'datarepository-detail', 'lookup_field': 'name'}}


class DataFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFormat
        fields = '__all__'
        extra_kwargs = {'url': {'view_name': 'dataformat-detail', 'lookup_field': 'name'}}


class DatasetTypeSerializer(serializers.HyperlinkedModelSerializer):
    created_by = serializers.SlugRelatedField(
        read_only=False,
        slug_field='username',
        queryset=get_user_model().objects.all(),
        allow_null=True,
        required=False,
        default=serializers.CurrentUserDefault(),
    )

    admin_url = serializers.SerializerMethodField()

    def get_admin_url(self,obj):
        return get_admin_url(obj)
    
    class Meta:
        model = DatasetType
        fields = ('id', 'name', 'created_by', 'description', 'filename_pattern', 'object', 'attribute','admin_url')
        extra_kwargs = {'url': {'view_name': 'datasettype-detail', 'lookup_field': 'name'}}


class FileRecordSerializer(serializers.HyperlinkedModelSerializer):
    dataset = serializers.PrimaryKeyRelatedField(
        read_only=False,
        queryset=Dataset.objects.all())

    admin_url = serializers.SerializerMethodField()

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related('dataset')
        return queryset

    def get_admin_url(self,obj):
        return get_admin_url(obj)

    class Meta:
        model = FileRecord
        fields = ['id',
                  'url',
                  'admin_url', 
                  'dataset', 
                  'json',
                  'file_name',
                  'full_path',
                  'relative_path',
                  'exists',
                  #ALF parts :
                  'remote_root', 
                  'attribute', 
                  'object', 
                  'extension', 
                  'revision', 
                  'collection', 
                  'subject', 
                  'date', 
                  'number', 
                  'extra',
                  ]
    

class DataRepositoryRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        if value is None :
            return None
        repository = DataRepository.objects.get(id=UUID(str(value)))
        return {
            'id': str(value),
            'name': repository.name,
        }
    
class DatasetFileRecordsSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileRecord
        fields = ('id', 'relative_path',  'extra', 'exists')

    # @staticmethod No longer necessary, but may be implemented elsewere to improve performance while getting FileRecord components
    # def setup_eager_loading(queryset):
    #     """ Perform necessary eager loading of data to avoid horrible performance."""
    #     queryset = queryset.select_related('data_repository', 'data_repository__globus_path') " 
    #     this only makes fething the related fields a single query process. As we don't fetch related fields anymore here it isn't necessary. We can do this for other models though"
    #     return queryset

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'

class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    created_by = serializers.SlugRelatedField(
        read_only=False, slug_field='username',
        queryset=get_user_model().objects.all(),
        default=serializers.CurrentUserDefault(),
    )

    dataset_type = serializers.SlugRelatedField(
        read_only=False, slug_field='name',
        queryset=DatasetType.objects.all(),
    )

    data_format = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field='file_extension',
        queryset=DataFormat.objects.all(),
    )

    revision_pk = serializers.SlugRelatedField(read_only=False, required=False,
                                            slug_field='pk',
                                            queryset=Revision.objects.all())

    revision = serializers.SerializerMethodField()

    session = serializers.SlugRelatedField(
        read_only=False, required=False, slug_field="pk",
        queryset=Session.objects.all(),
    )

    #session = serializers.HyperlinkedRelatedField(
    #    read_only=False, required=False, view_name="session-detail",
    #    queryset=Session.objects.all(),
    #)

    tags = serializers.SlugRelatedField(read_only=False, required=False, many=True,
                                        slug_field='name', queryset=Tag.objects.all())

    hash = serializers.CharField(required=False, allow_null=True)
    version = serializers.CharField(required=False, allow_null=True)
    file_size = serializers.IntegerField(required=False, allow_null=True)
    collection = serializers.CharField(required=False, allow_null=True)

    data_repository = DataRepositoryRelatedField(queryset=DataRepository.objects.all())

    
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

    def get_revision(self,obj):
        return obj.revision.name if obj.revision is not None else ""

    def get_admin_url(self,obj):
        return get_admin_url(obj)

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data to avoid horrible performance."""
        queryset = queryset.select_related(
            'created_by', 'dataset_type', 'data_format', 'session', 'data_repository', 'revision')
        queryset = queryset.prefetch_related(
            'file_records', 'tags')
        public = Count('tags', filter=Q(tags__public=True), output_field=BooleanField())
        protected = Count('tags', filter=Q(tags__protected=True), output_field=BooleanField())
        queryset = queryset.annotate(public=public, protected=protected)
        return queryset

    def create(self, validated_data):
        # Get out some useful info
        # revision = validated_data.get('revision', None)
        collection = validated_data.get('collection', None)
        name = validated_data.get('name', None)
        default = validated_data.get('default_dataset', None)
        session = validated_data.get('session', None)

        if session:
            if default is not False:
                _change_default_dataset(session, collection, name)
                validated_data['default_dataset'] = True
            return super(DatasetSerializer, self).create(validated_data)

        # Find or create an appropriate session for the dataset.
        subject = validated_data.pop('subject', None)
        date = validated_data.pop('date', None)
        if not subject or not date:
            return super(DatasetSerializer, self).create(validated_data)

        # Only get or create the appropriate session if at least the subject and
        # date are provided.
        number = validated_data.pop('number', None)
        user = validated_data.pop('created_by', None)

        session = _get_session(subject=subject, date=date, number=number, user=user)

        # Create the dataset, attached to the subsession.
        validated_data['session'] = session
        if default is not False:
            _change_default_dataset(session, collection, name)
            validated_data['default_dataset'] = True

        return super(DatasetSerializer, self).create(validated_data)
    
    class Meta:
        model = Dataset
        fields = ('id','url','admin_url', 'name', 'created_by', 'created_datetime',
                  'dataset_type', 'data_repository', 'data_format',
                  'session', 'file_size', 'hash', 'version',
                  'auto_datetime', 'revision_pk' ,
                  'default_dataset', 'protected', 'public', 'tags',
                  ## ALF PARTS (except extra)
                  'remote_root', 'subject', 'date', 'number',  'collection','revision', 'object', 'attribute', 'extension',
                  ##LIST OF FILE RECORDS
                  'file_records' )
        extra_kwargs = {
            'subject': {'write_only': True},
            'date': {'write_only': True},
            'number': {'write_only': True},
        }

class DownloadSerializer(serializers.HyperlinkedModelSerializer):

    # dataset = DatasetSerializer(many=False, read_only=True)
    dataset = serializers.PrimaryKeyRelatedField(many=False, read_only=True)

    user = serializers.SlugRelatedField(
        read_only=False, slug_field='username',
        queryset=LabMember.objects.all())

    class Meta:
        model = Download
        fields = ('id', 'user', 'dataset', 'count', 'json')


class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revision
        fields = '__all__'
