from django.urls import path
from . import views as subject_views

urlpatterns = [
    path("projects", subject_views.ProjectList.as_view(), name="project-list"),
    path("projects/<str:name>", subject_views.ProjectDetail.as_view(), name="project-detail"),
    path(
        "water-restricted-subjects",
        subject_views.WaterRestrictedSubjectList.as_view(),
        name="water-restricted-subject-list",
    ),
    path("subjects", subject_views.SubjectList.as_view(), name="subject-list"),
    path("subjects/<str:nickname>", subject_views.SubjectDetail.as_view(), name="subject-detail"),
]
