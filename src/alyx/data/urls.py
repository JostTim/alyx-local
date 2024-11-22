from django.urls import path
from . import views as data_views

register_file = data_views.RegisterFileViewSet.as_view({"post": "create"})

sync_file_status = data_views.SyncViewSet.as_view({"post": "sync", "get": "sync_status"})
new_download = data_views.DownloadViewSet.as_view({"post": "create"})

urlpatterns = [
    path("data-formats", data_views.DataFormatList.as_view(), name="dataformat-list"),
    path("data-formats/<str:name>", data_views.DataFormatDetail.as_view(), name="dataformat-detail"),
    path("data-repository-type", data_views.DataRepositoryTypeList.as_view(), name="datarepositorytype-list"),
    path(
        "data-repository-type/<str:name>",
        data_views.DataRepositoryTypeDetail.as_view(),
        name="datarepositorytype-detail",
    ),
    path("data-repository", data_views.DataRepositoryList.as_view(), name="datarepository-list"),
    path("data-repository/<str:name>", data_views.DataRepositoryDetail.as_view(), name="datarepository-detail"),
    path("revisions", data_views.RevisionList.as_view(), name="revision-list"),
    path("revisions/<str:name>", data_views.RevisionDetail.as_view(), name="revision-detail"),
    path("tags", data_views.TagList.as_view(), name="tag-list"),
    path("tags/<uuid:pk>", data_views.TagDetail.as_view(), name="tag-detail"),
    path("datasets", data_views.DatasetList.as_view(), name="dataset-list"),
    path("datasets/<uuid:pk>", data_views.DatasetDetail.as_view(), name="dataset-detail"),
    path("dataset-types", data_views.DatasetTypeList.as_view(), name="datasettype-list"),
    path("dataset-types/<str:name>", data_views.DatasetTypeDetail.as_view(), name="datasettype-detail"),
    path("downloads", data_views.DownloadList.as_view(), name="download-list"),
    path("downloads/<uuid:pk>", data_views.DownloadDetail.as_view(), name="download-detail"),
    path("files", data_views.FileRecordList.as_view(), name="filerecord-list"),
    path("files/<uuid:pk>", data_views.FileRecordDetail.as_view(), name="filerecord-detail"),
    path("new-download", new_download, name="new-download"),
    path("register-file", register_file, name="register-file"),
    path("sync-file-status", sync_file_status, name="sync-file-status"),
]
