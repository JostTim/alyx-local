from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from django.utils.functional import cached_property

from alyx.settings import TIME_ZONE, AUTH_USER_MODEL
from actions.models import Session
from alyx.base import BaseModel, modify_fields, BaseManager, CharNullField

import os, re


def _related_string(field):
    return "%(app_label)s_%(class)s_" + field + "_related"


# Data repositories
# ------------------------------------------------------------------------------------------------


class NameManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class DataRepositoryType(BaseModel):
    """
    A type of data repository, e.g. local SAMBA file server; web archive; LTO tape
    """

    objects = NameManager()

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return "<DataRepositoryType '%s'>" % self.name


class DataRepository(BaseModel):
    """
    A data repository e.g. a particular local drive, specific cloud storage
    location, or a specific tape.

    Stores an absolute path to the repository root as a URI (e.g. for SMB
    file://myserver.mylab.net/Data/ALF/; for web
    https://www.neurocloud.edu/Data/). Additional information about the
    repository can stored in JSON  in a type-specific manner (e.g. which
    cardboard box to find a tape in)
    """

    objects = NameManager()

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Nickname of the repository, to identify it",
    )

    repository_type = models.ForeignKey(
        DataRepositoryType, null=True, blank=True, on_delete=models.CASCADE
    )

    hostname = models.CharField(
        max_length=200,
        blank=True,
        validators=[
            RegexValidator(
                r"^[a-zA-Z0-9\.\-\_]+$",
                message="Invalid hostname",
                code="invalid_hostname",
            )
        ],
        help_text="Host name of the network drive. e.g. Mountcastle",
    )

    data_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL of the data repository, if it is accessible via HTTP (WebDav). You can leave it unspecified as it is currentely not used.",
    )

    @property
    def data_path(self):
        hostname = self.hostname.strip("/").strip(
            "\\"
        )  # removing back or forward slashes on both sides
        root = os.path.join("//" + hostname, self.globus_path.strip("/").strip("\\"))
        return root

    timezone = models.CharField(
        max_length=64,
        blank=True,
        default=TIME_ZONE,
        help_text="Timezone of the server "
        "(see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)",
    )

    globus_path = models.CharField(
        max_length=1000,
        blank=True,
        help_text="relative root path to the repository on the server, without the hostname. e.g. /lab/data/Adaptation",
    )

    globus_endpoint_id = models.UUIDField(
        blank=True, null=True, help_text="UUID of the globus endpoint"
    )

    globus_is_personal = models.BooleanField(
        null=False,
        blank=True,
        default=False,
        help_text="whether the Globus endpoint is personal or not. "
        "By default, Globus cannot transfer a file between two personal endpoints. The default value is False",
    )

    def __str__(self):
        return "<DataRepository '%s'>" % self.name

    class Meta:
        verbose_name_plural = "data repositories"
        ordering = ("name",)


# Datasets
# ------------------------------------------------------------------------------------------------


class DataFormat(BaseModel):
    """
    A descriptor to accompany a Dataset or DataCollection, saying what sort of information is
    contained in it. E.g. "Neuropixels raw data, formatted as flat binary file" "eye camera
    movie as mj2", etc. Normally each DatasetType will correspond to a specific 3-part alf name
    (for individual files) or the first word of the alf names (for DataCollections)
    """

    objects = NameManager()

    name = models.CharField(
        max_length=255, unique=True, help_text="short identifying name, e.g. 'npy'"
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable description of the file format e.g. 'npy-formatted square "
        "numerical array'.",
    )

    file_extension = models.CharField(
        blank=False,
        null=False,
        unique=True,
        max_length=255,
        validators=[
            RegexValidator(
                r"^\.[^\.]+$",
                message="Invalid file extension, should start with a dot",
                code="invalid_file_extension",
            )
        ],
        help_text="file extension, starting with a dot.",
    )

    matlab_loader_function = models.CharField(
        max_length=255, blank=True, help_text="Name of MATLAB loader function'."
    )

    python_loader_function = models.CharField(
        max_length=255, blank=True, help_text="Name of Python loader function'."
    )

    class Meta:
        verbose_name_plural = "data formats"
        ordering = ("name",)

    def __str__(self):
        return "<DataFormat '%s'>" % self.name

    def save(self, *args, **kwargs):
        """this is to trigger the update of the auto-date field"""

        self.name = self.file_extension.strip(".")
        self.file_extension = "." + self.name

        super(DataFormat, self).save(*args, **kwargs)


class DatasetType(BaseModel):
    """
    A descriptor to accompany a Dataset or DataCollection, saying what sort of information is
    contained in it. E.g. "Neuropixels raw data, formatted as flat binary file" "eye camera
    movie as mj2", etc. Normally each DatasetType will correspond to a specific 3-part alf name
    (for individual files) or the first word of the alf names (for DataCollections)
    """

    objects = NameManager()

    name = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=False,
        help_text="Short identifying nickname, e.g. 'spikes.times'",
    )

    object = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        validators=[
            RegexValidator(
                r"^[\w\-,;!#~&}{\]\[()]+$",
                message="Invalid object. Must not contain a dot (.)",
                code="invalid_object",
            )
        ],
        help_text="object (first part of the name) as per alf convention described here : https://int-brain-lab.github.io/ONE/alf_intro.html#dataset-name",
    )

    attribute = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        validators=[
            RegexValidator(
                r"^[\w\-,;!#~&}{\]\[()]+$",
                message="Invalid attribute. Must not contain a dot (.)",
                code="invalid_attribute",
            )
        ],
        help_text="attribute (second part of the name) as per alf convention",
    )

    created_by = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name=_related_string("created_by"),
        help_text="The creator of the data.",
    )

    # changed this to TextField
    description = models.TextField(
        max_length=1023,
        blank=True,
        help_text="Human-readable description of data type. Should say what is in the file, and "
        "how to read it. For DataCollections, it should list what Datasets are expected in the "
        "the collection. E.g. 'Files related to spike events, including spikes.times.npy, "
        "spikes.clusters.npy, spikes.amps.npy, spikes.depths.npy",
    )

    filename_pattern = CharNullField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="File name pattern (with wildcards) for this file in ALF naming convention. "
        "E.g. 'spikes.times.*' or '*.timestamps.*', or 'spikes.*.*' for a DataCollection, which "
        "would include all files starting with the word 'spikes'. NB: Case-insensitive matching."
        "If null, the name field must match the object.attribute part of the filename.",
    )

    file_location_template = models.JSONField(
        null=True,
        blank=True,
        help_text="Template to tell how the data of this type should be stored inside the session folder",
    )

    extras_description = models.CharField(
        blank=True,
        null=True,
        max_length=512,
        help_text="Description of what the extra refer to for all the files in this dataset. Should be null or one description ",
    )

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["object", "attribute"], name="unique_dataset_type"
            )
        ]  # this is redundant with the fact that name is unique=True but as name is set in save(), we still prefer to have this

    def __str__(self):
        return "<DatasetType %s>" % self.name

    def save(self, *args, **kwargs):
        """Ensure filename_pattern is lower case."""
        if self.filename_pattern:
            self.filename_pattern = self.filename_pattern.lower()

        if self.object and self.attribute:
            self.object = self.object.replace(".", "")
            self.attribute = self.attribute.replace(".", "")
            self.name = self.object + "." + self.attribute
        return super().save(*args, **kwargs)


class BaseExperimentalData(BaseModel):
    """
    Abstract base class for all data acquisition models. Never used directly.

    Contains an Session link, to provide information about who did the experiment etc. Note that
    sessions can be organized hierarchically, and this can point to any level of the hierarchy
    """

    session = models.ForeignKey(
        Session,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name=_related_string("session"),
        help_text="The Session to which this data belongs",
    )

    created_by = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name=_related_string("created_by"),
        help_text="The creator of the data.",
    )

    created_datetime = models.DateTimeField(
        blank=True, null=True, default=timezone.now, help_text="The creation datetime."
    )

    generating_software = models.CharField(
        max_length=255, blank=True, help_text="e.g. 'ChoiceWorld 0.8.3'"
    )

    provenance_directory = models.ForeignKey(
        "data.Dataset",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name=_related_string("provenance"),
        help_text="link to directory containing intermediate results",
    )

    class Meta:
        abstract = True


def default_dataset_type():
    return DatasetType.objects.get_or_create(name="unknown")[0].pk


def default_data_format():
    return DataFormat.objects.get_or_create(name="unknown")[0].pk


class Tag(BaseModel):
    objects = NameManager()
    name = models.CharField(
        max_length=255, blank=True, help_text="Long name", unique=True
    )
    description = models.CharField(max_length=1023, blank=True)
    protected = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    hash = models.CharField(
        blank=True,
        null=True,
        max_length=64,
        help_text=(
            "Hash of the data buffer, SHA-1 is 40 hex chars, while md5"
            "is 32 hex chars"
        ),
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return "<Tag %s>" % self.name


class Revision(BaseModel):
    """
    Dataset revision information
    """

    objects = NameManager()
    name = models.CharField(
        max_length=255, blank=True, help_text="Long name", unique=True
    )
    description = models.CharField(max_length=1023, blank=True)
    created_datetime = models.DateTimeField(
        blank=True, null=True, default=timezone.now, help_text="created date"
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return "<Revision %s>" % self.name

    @property
    def hashed(self):
        name = self.name
        return "#" + name + "#" if (self.name is not None and self.name != "") else ""


class DatasetManager(BaseManager):
    def get_queryset(self):
        qs = super(DatasetManager, self).get_queryset()
        qs = qs.select_related("dataset_type", "data_format")
        return qs


# @modify_fields(name={
#    'blank': False,
# })
class Dataset(BaseExperimentalData):
    """
    A chunk of data that is stored outside the database, most often a rectangular binary array.
    There can be multiple FileRecords for one Dataset, which will be different physical files,
    all having the same dataset-type.
    """

    objects = DatasetManager()

    file_size = models.BigIntegerField(blank=True, null=True, help_text="Size in bytes")
    # this shall be removed and moved to filerecord

    md5 = models.UUIDField(
        blank=True, null=True, help_text="MD5 hash of the data buffer"
    )
    # this shall be removed and moved to filerecord

    hash = models.CharField(
        blank=True,
        null=True,
        max_length=64,
        help_text=(
            "Hash of the data buffer, SHA-1 is 40 hex chars, while md5"
            "is 32 hex chars"
        ),
    )
    # this shall be removed and moved to filerecord

    # here we usually refer to version as an algorithm version such as ibllib-1.4.2, scanimage X.watever...
    # This fild should not be too important, as the dataset-type content description should not be not too wide
    # (if new version => new content in the file, just create a new dataset type instead of packing tons of possibilities inside one dataset-type)
    # and if changes in storage manner depending on version is made in a way that the most recent readers are retrocompatible.
    version = models.CharField(
        blank=True,
        null=True,
        max_length=64,
        help_text="version of the algorithm generating the file",
    )

    # the collection is the subfolder(s) inside the session folder, where files will be located
    collection = models.CharField(
        blank=True,
        default="",
        max_length=255,
        help_text="file subcollection or subfolder",
    )

    data_repository = models.ForeignKey(
        "DataRepository",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The data repository of all the files of this dataset. If left blank, it will use the default data repository of the session",
    )

    dataset_type = models.ForeignKey(
        DatasetType,
        blank=False,
        null=False,
        on_delete=models.SET_DEFAULT,
        default=default_dataset_type,
    )

    data_format = models.ForeignKey(
        DataFormat,
        blank=False,
        null=False,
        on_delete=models.SET_DEFAULT,
        default=default_data_format,
    )

    revision = models.ForeignKey(
        Revision, blank=True, null=True, on_delete=models.SET_NULL
    )

    tags = models.ManyToManyField("data.Tag", blank=True, related_name="datasets")

    auto_datetime = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name="last updated"
    )

    default_dataset = models.BooleanField(
        default=True, help_text="Whether this dataset is the default " "latest revision"
    )  # THIS SHOULD BE NAMED DEFAULT REVISIONS, NOT DEFAULT DATASET

    extras_description = models.CharField(
        blank=True,
        null=True,
        max_length=512,
        help_text="Description of what the extra refer to for all the files in this dataset. Should be null or one description ",
    )

    @property
    def is_online(self):
        fr = self.file_records
        if fr:
            return all(
                fr.values_list("exists", flat=True)
            )  # If we want this to be somewhat usefull, it should be a field that is checked regularly
            # (each week let's say. If the amount of file is not crazy, maybe each day during night ?)
            # by a worker and files "existance" should be updated at that time.
            # This may be usefull to probe for user error (like a massive deletion) and be able to react fast before the NAS backups are trashed.
        else:
            return False

    @property
    def is_protected(self):
        tags = self.tags.filter(protected=True)
        if tags.count() > 0:
            return True
        else:
            return False

    @property
    def is_public(self):
        tags = self.tags.filter(public=True)
        if tags.count() > 0:
            return True
        else:
            return False

    @property
    def object(self):
        return self.dataset_type.object

    @property
    def attribute(self):
        return self.dataset_type.attribute

    @property
    def extension(self):
        return self.data_format.file_extension

    @property
    def subject(self):
        return self.get_session_path(as_dict=True)["subject"]

    @property
    def date(self):
        return self.get_session_path(as_dict=True)["date"]

    @property
    def number(self):
        return self.get_session_path(as_dict=True)["number"]

    @property
    def remote_root(self):
        return self.data_repository.data_path

    def get_session_path(self, as_dict=False):
        # returns wm29/2023-05-25/002
        session_path = self.session.alias
        if not as_dict:
            return session_path

        patt = r"(?P<subject>[\w-]+)(?:\/|\\)(?P<date>\d{4}-\d{2}-\d{2})(?:\/|\\)(?P<number>\d{1,3})"
        spec = re.compile(patt)
        match = spec.search(session_path)
        if match is None:
            raise AttributeError(
                f"Session {self.session} alias {session_path} doesn't match the subject/date/nb pattern"
            )
        return dict(zip(spec.groupindex.keys(), match.groups()))

    def __str__(self):
        date = self.created_datetime.strftime("%d/%m/%Y at %H:%M")
        return "<Dataset %s %s '%s' by %s on %s>" % (
            str(self.pk)[:8],
            getattr(self.dataset_type, "name", ""),
            self.name,
            self.created_by,
            date,
        )

    def save(self, *args, **kwargs):
        # when a dataset is saved / created make sure the probe insertion is set in the reverse m2m

        def sanitize_folders(folder_field):
            if folder_field is None:
                return ""  # as it is a char field, we prefer saving an empty char rather than null when using no collection
            folder_field = folder_field.strip(".").strip("\\").strip("/")
            return (
                folder_field if folder_field == "" else os.path.normpath(folder_field)
            )

        self.collection = sanitize_folders(self.collection)

        if self.data_repository is None:
            if self.session.default_data_repository is None:
                self.data_repository = self.session.project.default_data_repository
            else:
                self.data_repository = self.session.default_data_repository

        query_set = self.__class__.objects.filter(
            dataset_type=self.dataset_type,
            session=self.session,
            collection=self.collection,
        )
        if self.id is not None:
            query_set = query_set.exclude(id=self.id)

        if query_set.count():
            raise ValidationError(
                "Two datasets for the same session with the same dataset type and collection cannot exist"
            )

        self.name = (
            self.dataset_type.object
            + "."
            + self.dataset_type.attribute
            + self.data_format.file_extension
        )

        super(Dataset, self).save(*args, **kwargs)

        # save childs file records to update the changed collection or dataset type, if necessary.
        file_records = FileRecord.objects.filter(dataset=self)

        for file_record in file_records:
            file_record.save()

        # if self.collection is None:
        #    return

        # from experiments.models import ProbeInsertion
        # I guess this is weird things for electrophy probe insertion features. Need to check if we want to remove it
        # (still in the process of having a clean version without too much weird intricacies)
        # parts = self.collection.rsplit('/')
        # if len(parts) > 1:
        #    name = parts[1]
        #    pis = ProbeInsertion.objects.filter(session=self.session, name=name)
        #    if len(pis):
        #        self.probe_insertion.set(pis.values_list('pk', flat=True))


# Files
# ------------------------------------------------------------------------------------------------
class FileRecordManager(models.Manager):
    def get_queryset(self):
        qs = super(FileRecordManager, self).get_queryset()
        qs = qs.select_related("dataset__data_repository")
        return qs


class FileRecord(BaseModel):
    """
    A single file on disk or tape. Normally specified by a path within an archive. If required,
    more details can be in the JSON
    """

    objects = FileRecordManager()

    dataset = models.ForeignKey(
        Dataset, related_name="file_records", on_delete=models.CASCADE
    )

    extra = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        db_column="extras",  # adding this to migrate from "extra" to extra without having to copy/delete the column
        # https://stackoverflow.com/questions/3498140/migrating-django-model-field-name-change-without-losing-data
        help_text="extra of the file, separated by '.' or null if no extra. Example : pupil.00001. Null will be converted to '' internally",
    )

    exists = models.BooleanField(
        default=False,
        help_text="Whether the file exists in the data repository",
    )

    relative_path = models.CharField(
        blank=True, default="", max_length=1000, help_text="path name within repository"
    )

    hash = models.CharField(
        blank=True,
        null=True,
        max_length=64,
        help_text=(
            "Hash of the data buffer, SHA-1 is 40 hex chars, while md5"
            "is 32 hex chars"
        ),
    )

    # METHODS RECALCULATING FROM SOURCES INSTEAD OF USING SAVED VERSIONS. USE FOR SAVING / UPDATING / SERIALIZING
    # EXAMPLE to illustrate all conditions below :
    # The file record is named //cajal/cajal_data2/ONE/Adaptation/wm29/2023-05-25/002/trials/test_folder/trials.eventTimeline.special.001.tdms

    # @cached_property cached property cannot work with methods needing arguments
    def get_session_path(self, as_dict=False):
        # returns wm29/2023-05-25/002
        session_path = self.dataset.session.alias
        if not as_dict:
            return session_path

        patt = r"(?P<subject>[\w-]+)(?:\/|\\)(?P<date>\d{4}-\d{2}-\d{2})(?:\/|\\)(?P<number>\d{1,3})"
        spec = re.compile(patt)
        match = spec.search(session_path)
        if match is None:
            raise AttributeError(
                f"Session {self.dataset.session} alias {session_path} doesn't match the subject/date/nb pattern"
            )
        return dict(zip(spec.groupindex.keys(), match.groups()))

    def get_relative_path(
        self,
    ):  # THIS IN THE ONLY FIELD THAT IS SAVED IN THE MODEL TABLE,FOR CHECKING THAT NO FILES HAVING THE SAME NAME EXISTS FOR A GIVEN SESSION
        # returns wm29/2023-05-25/002/trials/test_folder/trials.eventTimeline.special.001.tdms
        return os.path.join(
            self.get_session_path(),
            self.collection,
            self.get_revision(with_hash=True),
            self.file_name,
        )

    def get_extra(self, with_dot=False):
        # returns .special.001
        dot = "." if with_dot else ""
        return dot + self.extra if (self.extra is not None and self.extra != "") else ""

    def get_revision(self, with_hash=False):
        if with_hash:
            return (
                self.dataset.revision.hashed
                if self.dataset.revision is not None
                else ""
            )
        return self.dataset.revision.name if self.dataset.revision is not None else ""

    @property
    def subject(self):
        return self.get_session_path(as_dict=True)["subject"]

    @property
    def date(self):
        return self.get_session_path(as_dict=True)["date"]

    @property
    def number(self):
        return self.get_session_path(as_dict=True)["number"]

    # CALCULATED FIELDS, FOR SERIALIZING
    @property
    def collection(self):
        return self.dataset.collection if self.dataset.collection is not None else ""

    @property
    def revision(self):
        return self.get_revision()

    @property
    def object(self):
        return self.dataset.object

    @property
    def attribute(self):
        return self.dataset.attribute

    @property
    def extension(self):
        return self.dataset.data_format.file_extension

    @property
    def session_path(self):
        return self.get_session_path()

    @property  # THIS IS THE CALCULATED FIELD (not kept inside the base) of the full filename on the remote location only. Use relative_path to build a local path.
    def full_path(self):
        return os.path.join(self.remote_root, self.get_relative_path())

    @property
    def remote_root(self):
        return self.dataset.data_repository.data_path

    @property  # THIS IS THE CALCULATED FIELD (not kept inside the base) of the full filename on the remote location only. Use relative_path to build a local path.
    def file_name(self):
        return (
            self.object
            + "."
            + self.attribute
            + self.get_extra(with_dot=True)
            + self.extension
        )

    def save(self, *args, **kwargs):
        # check how to run this on change in data repository related, or
        # dataset collection related or
        # session related ?
        """this is to trigger the update of the auto-date field"""

        # self.file_name = self.get_filename()
        # self.relative_path = self.get_relative_path()

        self.extra = self.get_extra()
        self.relative_path = self.get_relative_path()

        query_set = self.__class__.objects.filter(relative_path=self.relative_path)
        if self.id is not None:
            query_set = query_set.exclude(id=self.id)
        if query_set.count():
            raise ValidationError(
                "Two files with the same session relative path cannot exist"
            )

        super(FileRecord, self).save(*args, **kwargs)
        # Save the dataset as well to make sure the auto datetime in the dateset is updated when
        # associated file record is saved
        # self.dataset.save()

    def __str__(self):
        return "<FileRecord '%s' by %s>" % (self.relative_path, self.dataset.created_by)


# Download table
# ------------------------------------------------------------------------------------------------


class Download(BaseModel):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    first_download = models.DateTimeField(auto_now_add=True)
    last_download = models.DateTimeField(auto_now=True)
    count = models.IntegerField(default=0)
    projects = models.ManyToManyField("subjects.Project", blank=True)

    class Meta:
        unique_together = (("user", "dataset"),)

    def increment(self):
        self.count += 1
        self.save()

    def __str__(self):
        return "<Download of %s dataset by %s (%d)>" % (
            self.dataset.dataset_type.name,
            self.user.username,
            self.count,
        )


def new_download(dataset, user, projects=()):
    d, _ = Download.objects.get_or_create(user=user, dataset=dataset)
    d.projects.add(*projects)
    d.increment()
    return d
