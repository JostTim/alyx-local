from django.urls import path, re_path
from django.views.generic.base import RedirectView
from .views import (
    ManagementHubView,
    ServicesHubView,
    DatabaseManagementUIView,
    CacheDownloadView,
    CacheVersionView,
    LabList,
    LabDetail,
    UserViewSet,
    NoteList,
    NoteDetail,
    MediaView,
)
from django.conf.urls import include


user_list = UserViewSet.as_view({"get": "list"})
user_detail = UserViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", RedirectView.as_view(url="/admin")),  # redirect the page to admin interface
    path("labs", LabList.as_view(), name="lab-list"),
    path("labs/<str:name>", LabDetail.as_view(), name="lab-detail"),
    path("notes", NoteList.as_view(), name="note-list"),
    path("notes/<uuid:pk>", NoteDetail.as_view(), name="note-detail"),
    path("users/<str:username>", user_detail, name="user-detail"),
    path("users", user_list, name="user-list"),
    re_path("^media/(?P<img_url>.*)", MediaView.as_view(), name="media"),
    path("cache.zip", CacheDownloadView.as_view(), name="cache-download"),
    re_path(r"^cache/info(?:/(?P<tag>\w+))?/$", CacheVersionView.as_view(), name="cache-info"),
    path("management", ManagementHubView.as_view(), name="management-hub"),
    path("management/database", DatabaseManagementUIView.as_view(), name="database-management"),
    path("management/media", DatabaseManagementUIView.as_view(), name="media-management"),
    path("management/restore", DatabaseManagementUIView.as_view(), name="restore-management"),
    path("management/backups", DatabaseManagementUIView.as_view(), name="backups-management"),
    path("services", ServicesHubView.as_view(), name="services-hub"),
]

try:
    # If ibl-reports redirect home to reports page
    urlpatterns += [
        path("ibl_reports/", include("ibl_reports.urls")),
    ]
    # urlpatterns += [path('', RedirectView.as_view(url='/ibl_reports/overview')), ]
except ModuleNotFoundError:
    pass
    # redirect the page to admin interface
    # urlpatterns += [path('', RedirectView.as_view(url='/admin')), ]
