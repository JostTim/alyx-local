from django.urls import path
from django.conf.urls import include
from . import views as action_views

from markdownx import urls as markdownx

urlpatterns = [
    path(
        "admin-actions/weighing-plot/<uuid:subject_id>",
        action_views.weighing_plot,
        name="weighing-plot",
    ),
    path(
        "admin-actions/training-perf-plot/<uuid:subject_id>",
        action_views.training_perf_plot,
        name="training-perf-plot",
    ),
    path(
        "admin-actions/water-history/<uuid:subject_id>",
        action_views.WaterHistoryListView.as_view(),
        name="water-history",
    ),
    path(
        "admin-actions/training-history/<uuid:subject_id>",
        action_views.TrainingHistoryListView.as_view(),
        name="training-history",
    ),
    path(
        "admin-actions/training/",
        action_views.TrainingListView.as_view(),
        name="training",
    ),
    path(
        "admin-actions/training/<date>",
        action_views.TrainingListView.as_view(),
        name="training",
    ),
    path(
        "admin-actions/subject-history/<uuid:subject_id>",
        action_views.SubjectHistoryListView.as_view(),
        name="subject-history",
    ),
    path("locations", action_views.LabLocationList.as_view(), name="location-list"),
    path(
        "locations/<str:name>",
        action_views.LabLocationAPIDetails.as_view(),
        name="location-detail",
    ),
    path("procedures", action_views.ProcedureTypeList.as_view(), name="procedures-list"),
    path("sessions", action_views.SessionAPIList.as_view(), name="session-list"),
    path("sessions/<uuid:pk>", action_views.SessionAPIDetail.as_view(), name="session-detail"),
    path("surgeries", action_views.SurgeriesList.as_view(), name="surgeries-list"),
    path(
        "water-administrations",
        action_views.WaterAdministrationAPIListCreate.as_view(),
        name="water-administration-create",
    ),
    path(
        "water-administrations/<uuid:pk>",
        action_views.WaterAdministrationAPIDetail.as_view(),
        name="water-administration-detail",
    ),
    path(
        "water-requirement/<str:nickname>",
        action_views.WaterRequirement.as_view(),
        name="water-requirement",
    ),
    path(
        "water-restriction",
        action_views.WaterRestrictionList.as_view(),
        name="water-restriction-list",
    ),
    path("water-type", action_views.WaterTypeList.as_view(), name="watertype-list"),
    path("water-type/<str:name>", action_views.WaterTypeList.as_view(), name="watertype-detail"),
    path("weighings", action_views.WeighingAPIListCreate.as_view(), name="weighing-create"),
    path("weighings/<uuid:pk>", action_views.WeighingAPIDetail.as_view(), name="weighing-detail"),
    path("markdownx/", include(markdownx)),
]
