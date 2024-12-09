from pathlib import Path
import os.path as op
import json
from mimetypes import guess_type
import urllib.parse
import requests

# from one.remote.aws import get_s3_virtual_host
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, FileResponse, JsonResponse, HttpResponseRedirect, HttpResponseNotFound, Http404
from django.views import View
from django.views.generic import TemplateView

from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from ..base.filters import BaseFilterSet
from ..base.permissions import rest_permission_classes
from ..data.models import Tag
from .serializers import UserSerializer, LabSerializer, NoteSerializer
from .models import Lab, Note
from ..base.settings import TABLES_ROOT, MEDIA_ROOT
from .filters import LabFilter

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

content_type = ContentType.objects.get_for_model(Permission)
permission = Permission.objects.get_or_create(
    codename="system_admin",
    content_type=content_type,
    defaults={
        "name": "Can manage the system via UI interface. Dangerous action, should be admin restricted only",
    },
)


@api_view(["GET"])
def api_root(request, format=None):
    """**[==========> CLICK HERE TO GO TO THE ADMIN INTERFACE <==========](/admin)**

    Welcome to Alyx's API! At the moment, there is read-only support for
    unauthenticated user lists, and authenticated read-write subject metadata
    and weighings. This should be reasonably self-documented; standard REST options
    are supported by sending an `OPTIONS /api/subjects/` for example. This is in alpha
    and endpoints are subject to change at short notice!

    **[ ===> Models documentation](/admin/doc/models)**

    """
    return Response(
        {
            "users-url": reverse("user-list", request=request, format=format),
            "subjects-url": reverse("subject-list", request=request, format=format),
            "sessions-url": reverse("session-list", request=request, format=format),
            "projects-url": reverse("project-list", request=request, format=format),
            "labs-url": reverse("lab-list", request=request, format=format),
            "datasets-url": reverse("dataset-list", request=request, format=format),
            "files-url": reverse("filerecord-list", request=request, format=format),
            "datarepository-url": reverse("datarepository-list", request=request, format=format),
            "datarepositorytype-url": reverse("datarepositorytype-list", request=request, format=format),
            "dataformat-url": reverse("dataformat-list", request=request, format=format),
            "dataset-types-url": reverse("datasettype-list", request=request, format=format),
            "register-file": reverse("register-file", request=request, format=format),
            "weighings-url": reverse("weighing-create", request=request, format=format),
            "water-restricted-subjects-url": reverse("water-restricted-subject-list", request=request, format=format),
            "water-administrations-url": reverse("water-administration-create", request=request, format=format),
            #'water-requirement-url': reverse(
            #    'water-requirement', request=request, format=format),
        }
    )


class UserViewSet(ReadOnlyModelViewSet):
    """
    Lists all users with the subjects which they are responsible for.
    """

    queryset = get_user_model().objects.all()
    queryset = UserSerializer.setup_eager_loading(queryset)
    serializer_class = UserSerializer
    lookup_field = "username"
    permission_classes = rest_permission_classes()


class LabList(ListCreateAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabSerializer
    permission_classes = rest_permission_classes()
    lookup_field = "name"
    filterset_class = LabFilter


class LabDetail(RetrieveUpdateDestroyAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabSerializer
    permission_classes = rest_permission_classes()
    lookup_field = "name"


class NoteList(ListCreateAPIView):
    """
    post:
    If an image is provided, the request body can contain an additional item

    `width`: desired width to resize the image for storage. Aspect ratio will be maintained.
    Options are

    - **None** to use the UPLOADED_IMAGE_WIDTH specified in settings (default)
    - **'orig'** to keep original image size
    - any **integer** to specify the image width
    """

    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = rest_permission_classes()
    filterset_class = BaseFilterSet


class NoteDetail(RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = rest_permission_classes()


class MediaView(APIView):
    permission_classes = rest_permission_classes()

    def get(self, request=None, format=None, img_url=""):
        path = op.join(MEDIA_ROOT, img_url)
        # return HttpResponse(path)

        if op.exists(path):
            content_type, _ = guess_type(path)
            if content_type is None:
                content_type = "application/octet-stream"
            return FileResponse(open(path, "rb"), content_type=content_type)
        else:
            return HttpResponseNotFound(f"Media not found at {path}")


def _get_cache_info(tag=None):
    """
    Load and return the cache info JSON file. Contains information such as cache table timestamp,
    size and API version.

    Assumes the following folder structure:
    <TABLES_ROOT>/
    ├─ cache_info.json
    ├─ cache.zip
    ├─ <DATASET_TAG_1>/
    │  ├─ cache_info.json
    │  ├─ cache.zip

    :param: optional tag name for fetching a specific cache
    :return: dict of cache table information
    """
    META_NAME = "cache_info.json"
    parsed = urllib.parse.urlparse(TABLES_ROOT)

    if tag:  # Validate
        Tag.objects.get(name=tag)

    scheme = parsed.scheme or "file"  # NB: 'file' only supported on POSIX filesystems
    if scheme == "file":
        # Cache table is local
        file_json_cache = Path(TABLES_ROOT).joinpath(tag or "", META_NAME)
        with open(file_json_cache) as fid:
            cache_info = json.load(fid)
    elif scheme.startswith("http"):
        cache_root = TABLES_ROOT.strip("/") + (f"/{tag}" if tag else "")
        file_json_cache = f"{cache_root}/{META_NAME}"
        resp = requests.get(file_json_cache)
        resp.raise_for_status()
        cache_info = resp.json()
        if "location" not in cache_info:
            cache_info["location"] = cache_root + "/cache.zip"
    elif scheme == "s3":
        # Use PyArrow to read file from s3
        from ..misc.management.commands.one_cache import _s3_filesystem

        s3 = _s3_filesystem()
        cache_root = parsed.netloc + "/" + parsed.path.strip("/") + (f"/{tag}" if tag else "")
        file_json_cache = f"{cache_root}/{META_NAME}"
        with s3.open_input_stream(file_json_cache) as stream:
            cache_info = json.load(stream)
        # if "location" not in cache_info:
        #     cache_info["location"] = get_s3_virtual_host(f"{cache_root}/cache.zip", region=s3.region)
    else:
        raise ValueError(f'Unsupported URI scheme "{scheme}"')

    return cache_info


class CacheVersionView(APIView):
    permission_classes = rest_permission_classes()

    def get(self, request=None, tag=None, **kwargs):
        try:
            return JsonResponse(_get_cache_info(tag))
        except Tag.DoesNotExist as ex:
            return HttpResponseNotFound(str(ex))


class CacheDownloadView(APIView):
    permission_classes = rest_permission_classes()

    def get(self, request=None, **kwargs):
        if TABLES_ROOT.startswith("http"):
            response = HttpResponseRedirect(TABLES_ROOT.strip("/") + "/cache.zip")
        else:
            cache_file = Path(TABLES_ROOT).joinpath("cache.zip")
            response = FileResponse(open(cache_file, "br"))
        return response


class ManagementHubView(TemplateView, LoginRequiredMixin, PermissionRequiredMixin):
    template_name = "management/hub.html"
    permission_required = "system_admin"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subpages"] = [
            {"name": "Database Management", "url": "database-management"},
            {"name": "Media Management", "url": "media-management"},
            {"name": "Backups", "url": "backups-management"},
            {"name": "Restore", "url": "restore-management"},
        ]
        context["site_header"] = "Alyx"
        context["title"] = "Management Hub"
        return context


class DatabaseManagementUIView(View, LoginRequiredMixin, PermissionRequiredMixin):
    template_name = "management/database.html"
    permission_required = "system_admin"
