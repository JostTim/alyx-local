from django.conf.urls import include
from django.urls import path
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

from rest_framework.authtoken import views as authv
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import adminsite

urlpatterns = [
    path("", include("alyx.misc.urls")),
    path("", include("alyx.experiments.urls")),
    path("", include("alyx.jobs.urls")),
    path("", include("alyx.actions.urls")),
    path("", include("alyx.data.urls")),
    path("", include("alyx.subjects.urls")),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", adminsite.admin.site.urls),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("auth-token", authv.obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("markdownx/", include("markdownx.urls")),
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("favicon.ico"))),
]

# # this is an optional app
# try:
#     urlpatterns += [
#         path("ibl_reports/", include("ibl_reports.urls")),
#     ]
# except ModuleNotFoundError:
#     pass
