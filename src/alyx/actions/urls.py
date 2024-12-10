from django.urls import path
from django.conf.urls import include
from .views import (
    SessionAPIList,
    SessionAPIDetail,
    SurgeriesList,
    WaterHistoryListView,
    TrainingHistoryListView,
    TrainingListView,
    SubjectHistoryListView,
    LabLocationList,
    LabLocationAPIDetails,
    ProcedureTypeList,
    WaterTypeList,
    WaterRestrictionList,
    WaterRequirement,
    WaterAdministrationAPIListCreate,
    WaterAdministrationAPIDetail,
    WeighingAPIDetail,
    WeighingAPIListCreate,
    training_perf_plot,
    weighing_plot,
)

from markdownx import urls as markdownx

urlpatterns = [
    path(
        "admin-actions/weighing-plot/<uuid:subject_id>",
        weighing_plot,
        name="weighing-plot",
    ),
    path(
        "admin-actions/training-perf-plot/<uuid:subject_id>",
        training_perf_plot,
        name="training-perf-plot",
    ),
    path(
        "admin-actions/water-history/<uuid:subject_id>",
        WaterHistoryListView.as_view(),
        name="water-history",
    ),
    path(
        "admin-actions/training-history/<uuid:subject_id>",
        TrainingHistoryListView.as_view(),
        name="training-history",
    ),
    path(
        "admin-actions/training/",
        TrainingListView.as_view(),
        name="training",
    ),
    path(
        "admin-actions/training/<date>",
        TrainingListView.as_view(),
        name="training",
    ),
    path(
        "admin-actions/subject-history/<uuid:subject_id>",
        SubjectHistoryListView.as_view(),
        name="subject-history",
    ),
    path("locations", LabLocationList.as_view(), name="location-list"),
    path(
        "locations/<str:name>",
        LabLocationAPIDetails.as_view(),
        name="location-detail",
    ),
    path("procedures", ProcedureTypeList.as_view(), name="procedures-list"),
    path("sessions", SessionAPIList.as_view(), name="session-list"),
    path("sessions/<uuid:pk>", SessionAPIDetail.as_view(), name="session-detail"),
    path("surgeries", SurgeriesList.as_view(), name="surgeries-list"),
    path(
        "water-administrations",
        WaterAdministrationAPIListCreate.as_view(),
        name="water-administration-create",
    ),
    path(
        "water-administrations/<uuid:pk>",
        WaterAdministrationAPIDetail.as_view(),
        name="water-administration-detail",
    ),
    path(
        "water-requirement/<str:nickname>",
        WaterRequirement.as_view(),
        name="water-requirement",
    ),
    path(
        "water-restriction",
        WaterRestrictionList.as_view(),
        name="water-restriction-list",
    ),
    path("water-type", WaterTypeList.as_view(), name="watertype-list"),
    path("water-type/<str:name>", WaterTypeList.as_view(), name="watertype-detail"),
    path("weighings", WeighingAPIListCreate.as_view(), name="weighing-create"),
    path("weighings/<uuid:pk>", WeighingAPIDetail.as_view(), name="weighing-detail"),
    path("markdownx/", include(markdownx)),
]
