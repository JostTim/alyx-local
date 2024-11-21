from django.urls import path
from ..subjects import views

urlpatterns = [
    path("projects", views.ProjectList.as_view(), name="project-list"),
    path("projects/<str:name>", views.ProjectDetail.as_view(), name="project-detail"),
    path(
        "water-restricted-subjects",
        views.WaterRestrictedSubjectList.as_view(),
        name="water-restricted-subject-list",
    ),
    path("subjects", views.SubjectList.as_view(), name="subject-list"),
    path("subjects/<str:nickname>", views.SubjectDetail.as_view(), name="subject-detail"),
]
