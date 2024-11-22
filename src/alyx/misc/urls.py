from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views as misc_views
from django.conf.urls import include


user_list = misc_views.UserViewSet.as_view({"get": "list"})
user_detail = misc_views.UserViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", RedirectView.as_view(url="/admin")),  # redirect the page to admin interface
    path("labs", misc_views.LabList.as_view(), name="lab-list"),
    path("labs/<str:name>", misc_views.LabDetail.as_view(), name="lab-detail"),
    path("notes", misc_views.NoteList.as_view(), name="note-list"),
    path("notes/<uuid:pk>", misc_views.NoteDetail.as_view(), name="note-detail"),
    path("users/<str:username>", user_detail, name="user-detail"),
    path("users", user_list, name="user-list"),
    re_path("^media/(?P<img_url>.*)", misc_views.MediaView.as_view(), name="media"),
    path("cache.zip", misc_views.CacheDownloadView.as_view(), name="cache-download"),
    re_path(r"^cache/info(?:/(?P<tag>\w+))?/$", misc_views.CacheVersionView.as_view(), name="cache-info"),
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
